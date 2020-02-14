import os
import struct
import threading
from collections import namedtuple
from random import randint, sample
from threading import Thread
from time import sleep, time

import usb.core
import usb.backend.libusb1

DIR = os.path.dirname(__file__)

def background(fn):
    """ Decorator for functions that should run in the background. """
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t
    return run

def find_devices():
    """ Return a dict of Gramophone devices with their serials as keys. """
    backend = usb.backend.libusb1.get_backend(find_library=lambda x: DIR+"/libusb-1.0.dll")
    devs = usb.core.find(backend=backend, idVendor=0x0483, idProduct=0x5750, find_all=True)

    devices = {}
    for dev in devs:
        G = Gramophone(dev, False)
        G.read_product_info()
        G.read_firmware_info()
        if G.product_info['name'] == 'GRAMO-01':
            ser = G.product_info['serial']
            devices[ser] = G

    return devices

class Packet(object):
    """
    A 64 byte data packet that can be sent to the Gramophone.
    
    :param target: 2 byte address of the target. source of the reply given to this packet
    :type target: [int, int]
    
    :param source: 2 byte address of the source. target of the reply given to this packet
    :type source: [int, int]
    
    :param cmd: Identifier of the command
    :type cmd: int
    
    :param payload: The payload for the command eg.: the value to write
    :type payload: list of ints
    
    :param msn: Any number. The reply packet's msn will be the same.
    :type msn: int

    """
    msn = 0
    def __init__(self, target, source, cmd, payload, msn=None):
        self.target = target
        self.source = source
        self.cmd = [cmd]
        self.payload = payload

        if msn is None:
            self.msn = [Packet.msn]
            Packet.msn += 1
            Packet.msn %= 256
        else:
            self.msn = [msn]

    def __repr__(self):
        return 'Packet(target={}, source={}, msn={}, cmd={}, payload={})'.format(
            self.target, self.source, self.msn, self.cmd, self.payload)

    @property
    def plen(self):
        return len(self.payload)

    @property
    def filler(self):
        return [0] * (65-self.plen-8)

    @property
    def encoded(self):
        return self.target + self.source + self.msn + self.cmd +\
            [self.plen] + self.payload + self.filler

    @classmethod
    def from_array(cls, array):
        array = list(array)
        target = array[0:2]
        source = array[2:4]
        msn = array[4]
        cmd = array[5]
        plen = array[6]
        payload = array[7:7+plen]

        return cls(target, source, cmd, payload, msn=msn)

class Gramophone(object):
    """
    Representation of a Gramophone device.

    :param device: The USB device.
    :type device: usb.core.Device

    :param verbose: If set to True the details of the communication are printed.
    :type verbose: bool
    """
    error_codes = {0x00: 'PACKET_FAIL_UNKNOWNCMD',
                   0x01: 'PACKET_FAIL_INVALIDCMDSYNTAX',
                   0x04: 'PACKET_FAIL_INVALIDPARAMSYNTAX',
                   0x05: 'PACKET_FAIL_RANGEERROR',
                   0x06: 'PACKET_FAIL_PARAMNOTFOUND',
                   0x07: 'PACKET_FAIL_VALIDFAIL',
                   0x08: 'PACKET_FAIL_ACCESSVIOLATION'}

    Parameter = namedtuple('Parameter', ['name', 'info', 'type'])
    parameters = {
        0x01: Parameter('VSEN3V3', 'Voltage on 3.3V rail.', 'float'),
        0x02: Parameter('VSEN5V', 'Voltage on 5V rail.', 'float'),
        0x03: Parameter('TSENMCU', 'Internal teperature of the MCU.', 'float'),
        0x04: Parameter('TSENEXT', 'External temperature sensor on the board.', 'float'),
        0x0A: Parameter('SENSORS', 'The voltages and temperatures in one parameter', 'combo'),
        0x0B: Parameter('VOLTAGES', 'The voltages in one parameter', 'combo'),
        0x0C: Parameter('TEMPS', 'The temperatures in one parameter', 'combo'),
        0x05: Parameter('TIME', 'The time of the internal clock of the device.', 'uint64'),
        0x10: Parameter('ENCPOS', 'Encoder position.', 'int32'),
        0x11: Parameter('ENCVEL', 'Encoder velocity.', 'vel'),
        0x12: Parameter('ENCVELWIN', 'Encoder velocity window size.', 'uint16'),
        0x13: Parameter('ENCHOME', 'Encoder homing.', 'uint8'),
        0x14: Parameter('ENCHOMEPOS', 'Encoder home position.', 'int32'),
        0x20: Parameter('DI-1', 'Digital input 1.', 'uint8'),
        0x21: Parameter('DI-2', 'Digital input 2.', 'uint8'),
        0x25: Parameter('DI', 'Digital inputs.', 'combo'),
        0x30: Parameter('DO-1', 'Digital output 1.', 'uint8'),
        0x31: Parameter('DO-2', 'Digital output 2.', 'uint8'),
        0x32: Parameter('DO-3', 'Digital output 3.', 'uint8'),
        0x33: Parameter('DO-4', 'Digital output 4.', 'uint8'),
        0x35: Parameter('DO', 'Digital outputs.', 'combo'),
        0x40: Parameter('AO', 'Analogue output.', 'float'),
        0xFF: Parameter('LED', 'LED state changed', 'uint8'),
        0xAA: Parameter('REC', 'Bundle of parameters for the Recorder module.', 'combo'),
        0xBB: Parameter('LINM', 'Bundle of parameters for the LinMaze module.', 'combo')
                  }

    type_lengths = {'float': 4,
                    'double': 8,
                    'uint8': 1,
                    'uint16': 2,
                    'uint32': 4,
                    'uint64': 8,
                    'int8': 1,
                    'int16': 2,
                    'int32': 4,
                    'int64': 8,
                    'vel': 5
                    }

    combos = {
        0x0A:[0x01, 0x02, 0x03, 0x04], # Sensors
        0x0B:[0x01, 0x02], # Voltages
        0x0C:[0x03, 0x04], # Temperatures
        0x25:[0x20, 0x21], # Digital inputs
        0x35:[0x30, 0x31, 0x32, 0x33], # Digital outputs
        0xAA:[0x05, 0x11, 0x20, 0x21, 0x30, 0x31, 0x32, 0x33], # Time, vel, io
        0xBB:[0x05, 0x10, 0x20, 0x21, 0x30, 0x31, 0x32, 0x33]  # Time, pos, io
        }

    device_states = {0x00: 'IAP', 0x01: 'Application'}

    def __init__(self, device, verbose=False):
        self.device = device
        self.device.set_configuration()

        self.verbose = verbose


        self.target = [randint(0x00, 0xFF), randint(0x00, 0xFF)]
        self.source = [randint(0x00, 0xFF), randint(0x00, 0xFF)]
        self.firmware_info = None
        self.product_info = None
        self.dev_state = 'Unknown'

        self.bursting = {1: False,
                         2: False,
                         3: False,
                         4: False}

        self.readers = []

    def decode_payload(self, param_id, payload):
        """
        Decodes the given payload based on the type of the parameter.

        :param param_id: The key for the parameter dict. See: Gramophone.parameters
        :type param_id: int

        :param payload: The payload that will be decoded
        :type payload: list
        """
        if self.parameters[param_id].type == 'float':
            return struct.unpack('f', bytes(payload))[0]

        if self.parameters[param_id].type in ['int8', 'int16', 'int32', 'int64']:
            return int.from_bytes(payload, 'little', signed=True)

        if self.parameters[param_id].type in ['uint8', 'uint16', 'uint32', 'uint64']:
            return int.from_bytes(payload, 'little', signed=False)

        if self.parameters[param_id].type == 'vel':
            return struct.unpack('f', bytes(payload[0:4]))[0]*float(payload[4])

        if self.parameters[param_id].type == 'combo':
            I = 0
            values = {}
            for elemet_id in self.combos[param_id]:
                e_type = self.parameters[elemet_id].type
                length = self.type_lengths[e_type] 
                element = self.decode_payload(elemet_id, payload[I:I+length])
                I += length
                values[elemet_id] = element
            return values

    def read_input(self, input_id):
        """
        Read the state of a digital input.

        :param input_id: The number of the digital input (1 or 2)
        :type input_id: int

        :returns: 0 if the input is low, 1 if it is high
        :rtype: int
        """
        return self.read_param(0x20+input_id-1)

    def read_inputs(self):
        """
        Read the state of all digital inputs.

        :returns: dict with input numbers as keys, and their states as values. eg: {1:1, 2:1} when both inputs are high
        :rtype: dict
        """
        return self.read_params(0x25)

    def read_output(self, output_id):
        """
        Read the state of a digital output.

        :param output_id: The number of the digital output (1 to 4)
        :type output_id: int

        :returns: 0 if the output is low, 1 if it is high
        :rtype: int
        """
        return self.read_param(0x30+output_id-1)

    def read_outputs(self):
        """
        Read the state of all digital outputs.

        :returns: dict with output numbers as keys, and their states as values. eg: {1:0, 2:0, 3:0, 4:0} when both outputs are low
        :rtype: dict
        """
        return self.read_params(0x35)

    def read_analog_out(self):
        """
        Read the voltage of the analog output.

        :returns: The voltage the analog output is set to.
        :rtype: float
        """
        return self.read_param(0x40)
        
    def read_sensors(self):
        """
        Read the values from the voltage and temperature sensors.
        
        :returns: A dict with the parameter ids as keys. See: Gramophone.parameters
        :rtype: dict
        """
        return self.read_params(0x0A)

    def read_voltages(self):
        """
        Read the values from the voltage sensors.
        
        :returns: A dict with the parameter ids as keys. See: Gramophone.parameters
        :rtype: dict
        """
        return self.read_params(0x0B)

    def read_temperatures(self):
        """
        Read the values from the temperature sensors.
        
        :returns: A dict with the parameter ids as keys. See: Gramophone.parameters
        :rtype: dict
        """
        return self.read_params(0x0C)

    def read_time(self):
        """
        Read the time from the Gramophone's clock

        :returns: Time in ms/10
        :rtype: int
        """
        return self.read_param(0x05)

    def read_position(self):
        """
        Read the position register of the Gramophone.

        :returns: The position in counts travelled (1 full rotation = 14400 counts)
        :rtype: int
        """
        return self.read_param(0x10)

    def read_velocity(self):
        """
        Read the velocity of the Gramophones disk. Velocity is averaged in a window with a set size.

        :returns: Velocity in counts/sec (1 full rotation = 14400 counts)
        :rtype: 
        """
        return self.read_param(0x11)

    def read_window_size(self):
        """
        Read the window size of the velocity calculation, ie. how many position differences are averaged to
        get the velocity. Larger windows result in smoother velocity but slower response.

        :retruns: The window size
        :rtype: int
        """
        return self.read_param(0x12)

    def read_homing_state(self):
        """
        Reads wheter the device is homing. A home position can be set and this value changes when it is reached.
        0 if the encoder is not trying to find the home position, 
        1 if it is homing and 2 if the home position was found. 

        :returns: 0, 1 or 2 dependin on the state
        :rtype: int
        """
        return self.read_param(0x13)

    def read_homing_position(self):
        """
        The home postion that can be found by homing.
        
        :returns: The position
        :rtype: int
        """
        return self.read_param(0x14)

    def read_firmware_info(self):
        """ 
        Read the firmware information from the Gramophone.
        Sets the fimware related variables of the object.

        :returns: A dictionary with the firmware info fields in a human readable format.
        :rtype: dict
        """
        ask_firmware = Packet(self.target, self.source, 0x04, [])
        firmware_packet = self.send(ask_firmware)
        payload = firmware_packet.payload

        firmware_release = payload[0]
        firmware_sub = payload[1]
        firmware_build = int.from_bytes(payload[2:4], 'little', signed=False)
        firmware_year = int.from_bytes( payload[4:6], 'little', signed=False)
        firmware_month = payload[6]
        firmware_day = payload[7]
        firmware_hour = payload[8]
        firmware_minute = payload[9]
        firmware_second = payload[10]

        info = {
            'release': str(firmware_release)+'.'+str(firmware_sub),
            'build': str(firmware_build),
            'date': str(firmware_day)+'/'+str(firmware_month).zfill(2)+'/'+str(firmware_year).zfill(2),
            'time': str(firmware_hour)+':'+str(firmware_minute)+':'+str(firmware_second),
            'date_format': 'dd/mm/yyyy',
            'time_format': '24h'
            }

        if self.verbose:
            print('Firmware version:')
            print(' -Relase:', info['release'])
            print(' -Build:', info['build'])
            print(' -Date ({}): {}'.format(info['date_format'], info['date']))
            print(' -Time ({}): {}'.format(info['time_format'], info['time']))

        self.firmware_info = info
        return info

    def read_product_info(self):
        """ 
        Read the product information from the Gramophone.
        Sets the product related variables of the object.

        :returns: A dictionary with the product info fields in a human readable format.
        :rtype: dict
        """
        ask_product_info = Packet(self.target, self.source, 0x08, [])
        product_info_packet = self.send(ask_product_info)
        payload = product_info_packet.payload

        product_name = ''.join([chr(byte) for byte in payload[0:18] if byte != 0x00])
        product_revision = ''.join([chr(byte) for byte in payload[18:24]])
        product_serial = int.from_bytes(payload[24:28], 'little', signed=False)
        product_year = int.from_bytes(payload[28:30], 'little', signed=False)
        product_month = int.from_bytes(payload[30:31], 'little', signed=False)
        product_day = int.from_bytes(payload[31:32], 'little', signed=False)

        info = {
            'name': product_name,
            'revision': product_revision,
            'serial': product_serial, 
            'production': str(product_day).zfill(2)+'/'+str(product_month).zfill(2)+'/'+str(product_year),
            'production_format':'dd/mm/yyyy'
        }

        if self.verbose:
            print('Product info:')
            print(' -Name:', info['name'])
            print(' -Revision:', info['revision'] )
            print(' -Serial:', hex(info['serial']))
            print(' -Production ({}): {}'.format(info['production_format'], info['production']))

        self.product_info = info
        return info

    def read_recorder_params(self):
        """
        Read the parameters for the Recorder module. Time, velocity, and IO combined.

        :retruns: A dict with the read parameters, with ids as keys
        :rtype: dict
        """
        return self.read_params(0xAA)

    def read_linmaze_params(self):
        """ 
        Read the parameters for the LineMaze module. Time, position, and IO combined.

        :retruns: A dict with the read parameters, with ids as keys
        :rtype: dict
        """
        return self.read_params(0xBB)

    def read_dev_state(self):
        """ 
        Read the state of the device. The device should be in 0x01 state for usage.
        The 0x00 state is for setup.

        :returns: The device state. 'Application' or 'IAP'
        :rtype: str
        """
        ask_dev_state = Packet(self.target, self.source, 0x05, [])
        dev_state = self.send(ask_dev_state)
        self.dev_state = dev_state.payload[0]
        state = self.device_states[self.dev_state]
        if self.verbose:
            print('Device state:', state)

        return state

    def write_output(self, output, value):
        """Set the given output to a given state, eg. output 1 to 1 (high). 
        
        :param output: The output to set (1 to 4)
        :type output: int

        :param value: The state to set (1 is high, 0 is low)
        :type value: int
        """
        self.write_param(0x30+output-1, [int(value)])

    def write_analog(self, value):
        """
        Set the analog output to the given voltage, eg. to 2.1 V

        :param value: The voltage that will be set.
        :type value: float
        """
        self.write_param(0x40, list(struct.pack('f', value)))

    def ping(self):
        """ Send a ping packet with 5 bytes and print the time the process took. """
        rdata = sample(range(0, 255), 5)
        ping_time = time()
        ping_packet = Packet(self.target, self.source, 0x00, rdata)
        pong_packet = self.send(ping_packet)
        took = (time()-ping_time)*1000
        print('Ping!', ping_packet.payload)
        print('Pong!', pong_packet.payload)
        print('Took:', took, 'ms')

    def reset(self):
        """ Reset the device. Returns None if successful and the error string otherwise. """
        reset_command = Packet(self.target, self.source, 0xF0, [])
        response = self.send(reset_command)
        err = self.decode_response(response)
        if self.verbose:
            if err is None:
                print('Reset successful...')
            else:
                print(err)

        return err

    def decode_response(self, response):
        """
        Decodes a response. Returns the error message if the command 
        was not successful and None otherwise.

        :param response: The response to decode.
        :ptype response: Packet
        """
        if response.cmd[0] == 0x01:
            return None
        if response.cmd[0] == 0x02:
            return self.error_codes[response.payload[0]]
            
    def reset_time(self):
        """ Reset the Gramophone's internal clock to 0. """
        self.write_param(0x05, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    def reset_position(self):
        """ Reset the Gramophone's internal position counter to 0. """
        self.write_param(0x10, [0x00, 0x00, 0x00, 0x00])

    def read_param(self, param_id):
        """
        Read a single parameter and return its value.
        
        :param param_id: The id of the parameter that should be read.
        :type param_id: int

        :returns: The value of the parameter
        :rtype: depends on the parameter, see: Gramophone.parameters
        """
        ask_param = Packet(self.target, self.source, 0x0B, [param_id])
        payload = self.send(ask_param).payload

        if payload is not None:
            val = self.decode_payload(param_id, payload)
        if self.verbose:
            print(self.parameters[param_id].name, '=', val)

        return val

    def read_params(self, combo_id):
        """ Read multiple parameters and return them in a dict. """
        ask_params = Packet(self.target, self.source, 0x0B, self.combos[combo_id])
        payload = self.send(ask_params).payload
        values = self.decode_payload(combo_id, payload)

        if self.verbose:
            for key in self.combos[combo_id]:
                print(self.parameters[key].name, '=', values[key])
        
        return values

    def write_param(self, param, payload):
        """ Write the given payload into the given parameter. """
        set_param = Packet(self.target, self.source, 0x0C, [param]+payload)
        response = self.send(set_param)

        if self.verbose:
            if response.cmd[0] == 0x01:
                print('Writing', self.parameters[param].name, 'succeeded.')
            if response.cmd[0] == 0x02:
                print('Writing', self.parameters[param].name, 'failed.',
                      self.error_codes[response.payload[0]])

    def send(self, packet):
        """
        Sends a Packet to the device.

        :param packet: The Packet to send.
        :ptype packet: Packet
        """
        try:
            self.device.write(0x01, packet.encoded)
            while True:
                resp = Packet.from_array(self.device.read(0x81, 64))
                if resp.target == self.source and \
                        resp.source == self.target and \
                        resp.msn == packet.msn:
                    return resp

        except usb.core.USBError as usb_error:
            raise GramophoneError(usb_error)

    @background
    def start_burst(self, port, on_time, pause_time):
        """
        Start turning the given port on and off in the background.

        :param port: The port that will be turned on and off
        :type port: int (1-4)

        :param on_time: How long should the port be on (high) in seconds
        :type on_time: float

        :param pause_time: How long should the port be off (low) in seconds
        :type pause_time: float
        """
        self.bursting[port] = True
        while self.bursting[port]:
            self.write_output(port, 1)
            sleep(on_time)
            self.write_output(port, 0)
            sleep(pause_time)

    def stop_burst(self, port):
        """
        Stop turning the given port on and off. see: start_burst

        :param port: The port that will stop being turned on and off
        :type port: int (1-4)
        """
        self.bursting[port] = False
        

class GramophoneError(Exception):
    """ Exception for Gramophone related communication errors. """
    pass