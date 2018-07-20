import struct
import threading
from collections import namedtuple
from random import randint, sample
from threading import Thread
from time import sleep, time

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from pywinusb import hid


def background(fn):
    """ Decorator for functions that should run in the background. """
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t
    return run

def find_devices():
    dev_filter = hid.HidDeviceFilter(vendor_id=0x0483, product_id=0x5750)
    devices = {}
    for dev in dev_filter.get_devices():
        gram = Gramophone(dev, verbose=False)
        gram.open()
        for _ in range(5):
            gram.read_sensors()
            gram.read_firmware_info()
            gram.read_product_info()
            sleep(0.1)
            if gram.product_name == 'GRAMO-01':
                devices[gram.product_serial] = gram
                break
        gram.close()
    return devices

class Transmitter(QObject):
    """
    Emits Qt signals to transmit infromation from incoming packets.
    """
    velocity_signal = pyqtSignal(float)
    position_signal = pyqtSignal(int)
    position_diff_signal = pyqtSignal(int)
    inputs_signal = pyqtSignal(int, int)
    recorder_signal = pyqtSignal(int, float, int, int, int, int, int, int)
    device_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.last_pos = 0

    def emit_velocity(self, vel):
        """ 
        Emit a signal with the given velocity.

        :param vel: The velocity that should be emitted.
        :type vel: float
        """
        self.velocity_signal.emit(vel)

    def emit_position(self, pos):
        """ 
        Emit a signal with the given position.

        :param pos: The position that should be emitted.
        :type pos: int
        """
        self.position_signal.emit(pos)
        self.position_diff_signal.emit(pos-self.last_pos)
        self.last_pos = pos

    def emit_inputs(self, inputs):
        """ 
        Emit a signal with the state of the digital inputs.

        :param inputs: A list containing the states of the two digital inputs.
        :type inputs: [int, int]
        """
        self.inputs_signal.emit(inputs[0], inputs[1])

    def emit_recorder(self, values):
        """ 
        Emit a signal with all the data required by the Recorder module.
        These are the current time, velocity, input- and output states in order.

        :param values: A list containing the time, velocity, input- and output states.
        :type values: [int, float, int, int, int, int, int, int]
        """
        self.recorder_signal.emit(values[0], values[1],
                                  values[2], values[3],
                                  values[4], values[5],
                                  values[6], values[7])

    def emit_device_error(self, error_msg):
        """ 
        Emit a signal with the given error message.

        :param error_msg: The error message.
        :type error_msg: str
        """
        self.device_error.emit(str(error_msg))


class Reader(QObject):
    """
    A worker that can continnously send commands to the Gramophone with a given frequency.

    :param name: The name of this reader. Can be used for identification to stop a specific reader.
    :type name: str

    :param read_func: The read function that should be called.
    :type read_func: function

    :param frequency: The frequency at which the function should be called in Hz.
    :type frequency: float
    """
    def __init__(self, name, read_func, frequency):
        super().__init__()
        self.name = name
        self.read_func = read_func
        self.reading = None
        self.frequency = frequency

    @pyqtSlot()
    def read(self):
        """ Start calling the read function repeatedly. Slot for a QThread. """
        self.reading = True
        while self.reading:
            self.read_func()
            sleep(1/self.frequency)

    def abort(self):
        """ Stop calling the read function. """
        self.reading = False


class Gramophone(hid.HidDevice):

    error_codes = {0x00: 'PACKET_FAIL_UNKNOWNCMD',
                   0x01: 'PACKET_FAIL_INVALIDCMDSYNTAX',
                   0x04: 'PACKET_FAIL_INVALIDPARAMSYNTAX',
                   0x05: 'PACKET_FAIL_RANGEERROR',
                   0x06: 'PACKET_FAIL_PARAMNOTFOUND',
                   0x07: 'PACKET_FAIL_VALIDFAIL',
                   0x08: 'PACKET_FAIL_ACCESSVIOLATION'}

    Parameter = namedtuple('Parameter', ['name', 'info', 'type'])
    parameters = {0x01: Parameter('VSEN3V3', 'Voltage on 3.3V rail.', 'float'),
                  0x02: Parameter('VSEN5V', 'Voltage on 5V rail.', 'float'),
                  0x03: Parameter('TSENMCU', 'Internal teperature of the MCU.', 'float'),
                  0x04: Parameter('TSENEXT', 'External temperature sensor on the board.', 'float'),
                  0x0A: Parameter('SENSORS', 'The voltages and temperatures in one parameter', 'float_list'),
                  0x05: Parameter('TIME', 'The time of the internal clock of the device.', 'uint64'),
                  0x10: Parameter('ENCPOS', 'Encoder position.', '-int32'),
                  0x11: Parameter('ENCVEL', 'Encoder velocity.', 'vel_struct'),
                  0x12: Parameter('ENCVELWIN', 'Encoder velocity window size.', 'uint16'),
                  0x13: Parameter('ENCHOME', 'Encoder homing.', 'uint8'),
                  0x14: Parameter('ENCHOMEPOS', 'Encoder home position.', '-int32'),
                  0x20: Parameter('DI-1', 'Digital input 1.', 'uint8'),
                  0x21: Parameter('DI-2', 'Digital input 2.', 'uint8'),
                  0x25: Parameter('DI', 'Digital inputs.', 'list'),
                  0x30: Parameter('DO-1', 'Digital output 1.', 'uint8'),
                  0x31: Parameter('DO-2', 'Digital output 2.', 'uint8'),
                  0x32: Parameter('DO-3', 'Digital output 3.', 'uint8'),
                  0x33: Parameter('DO-4', 'Digital output 4.', 'uint8'),
                  0x35: Parameter('DO', 'Digital outputs.', 'list'),
                  0x40: Parameter('AO', 'Analogue output.', 'float'),
                  0xFF: Parameter('LED', 'LED state changed', 'uint8'),
                  0xAA: Parameter('REC', 'Bundle of parameters for the Recorder module.', 'recorder'),
                  0xBB: Parameter('LINM', 'Bundle of parameters for the LinMaze module.', 'linmaze')
                  }


    def __init__(self, device, verbose=False):
        self.device = device
        super().__init__(self.device.device_path,
                         self.device.parent_instance_id,
                         self.device.instance_id)

        self.verbose = verbose

        self.report = None
        self.set_raw_data_handler(self.data_handler)

        self.transmitter = Transmitter()
        self.readers = []

        self.target = [randint(0x00, 0xFF), randint(0x00, 0xFF)]
        self.source = [randint(0x00, 0xFF), randint(0x00, 0xFF)]

        self.ping_time = None
        self.app_state = 'Unknown'
        self.is_open = False

        self.firmware_release = None
        self.firmware_sub = None
        self.firmware_build = None
        self.firmware_year = None
        self.firmware_month = None
        self.firmware_day = None
        self.firmware_hour = None
        self.firmware_minute = None
        self.firmware_second = None

        self.product_name = None
        self.product_revision = None
        self.product_serial = None
        self.product_year = None
        self.product_month = None
        self.product_day = None

        self.last_position = 0
        self.last_time = 0
        self.last_velocity = 0
        self.last_in_1 = 0
        self.last_in_2 = 0
        self.last_out_1 = 0
        self.last_out_2 = 0
        self.last_out_3 = 0
        self.last_out_4 = 0

        self.bursting = {1: False,
                         2: False,
                         3: False,
                         4: False}
        self.burst_threads = []

        self.sensor_values = {'VSEN3V3': None,
                              'VSEN5V': None,
                              'TSENMCU': None,
                              'TSENEXT': None}

    def open(self):
        """ Connect to this device. """
        super().open()
        reports = self.find_output_reports()
        self.report = reports[0]
        self.check_app()
        sleep(0.1)
        if self.app_state == 'IAP':
            print('Device in IAP state. Resetting...')
            self.reset()
            sleep(0.1)
        self.is_open = True

    def close(self):
        """ Disconnect from this device. """
        self.report = None
        super().close()
        self.is_open = False

    @staticmethod
    def decode_payload(val_type, payload):
        if val_type == 'float':
            return struct.unpack('f', payload)[0]
        if val_type == 'float_list':
            float_list = []
            for I in range(len(payload)//4):
                float_list.append(struct.unpack('f', payload[I*4:I*4+4])[0])
            return float_list
        if val_type == 'int32':
            return int.from_bytes(payload, 'little', signed=True)
        if val_type == '-int32':
            return -int.from_bytes(payload, 'little', signed=True)
        if val_type in ['uint8', 'uint16', 'uint64']:
            return int.from_bytes(payload, 'little', signed=False)
        if val_type == 'vel_struct':
            return -struct.unpack('f', payload[0:4])[0]*float(payload[4])
        if val_type == 'list':
            return list(payload)
        if val_type == 'recorder':
            recorder_data = [] # time, vel, in_1, in_2,  out_1, out_2, out_3, out_4
            recorder_data.append(int.from_bytes(
                payload[0:8], 'little', signed=False))
            recorder_data.append(-struct.unpack(
                'f', payload[8:12])[0]*float(payload[12]))
            recorder_data.append(payload[13])
            recorder_data.append(payload[14])

            recorder_data.append(payload[15])
            recorder_data.append(payload[16])
            recorder_data.append(payload[17])
            recorder_data.append(payload[18])

            return recorder_data

        if val_type == 'linmaze':
            linmaze_data = [] # time, pos, in_1, in_2, out_1, out_2, out_3, out_4
            linmaze_data.append(int.from_bytes(
                payload[0:8], 'little', signed=False))
            linmaze_data.append(-int.from_bytes(
                payload[8:12], 'little', signed=True))
            linmaze_data.append(payload[12])
            linmaze_data.append(payload[13])

            linmaze_data.append(payload[14])
            linmaze_data.append(payload[15])
            linmaze_data.append(payload[16])
            linmaze_data.append(payload[17])
            return linmaze_data

        return None

    def read_input(self, input_id):
        self.read_param(0x20+input_id-1)

    def read_inputs(self):
        self.read_params(0x25, [0x20, 0x21])

    def read_output(self, output_id):
        self.read_param(0x30+output_id-1)

    def read_outputs(self):
        self.read_params(0x35, [0x30, 0x31, 0x32, 0x33])

    def read_analog_out(self):
        self.read_param(0x40)

    def read_voltages(self):
        self.read_param(0x01)
        self.read_param(0x02)

    def read_temperatures(self):
        self.read_param(0x03)
        self.read_param(0x04)

    def read_sensors(self):
        self.read_params(0x0A, [0x01, 0x02, 0x03, 0x04])

    def read_time(self):
        self.read_param(0x05)

    def read_position(self):
        self.read_param(0x10)

    def read_velocity(self):
        self.read_param(0x11)

    def read_window_size(self):
        self.read_param(0x12)

    def read_homing_state(self):
        self.read_param(0x13)
        self.read_param(0x14)

    def read_firmware_info(self):
        self.send(0x00, 0x04, [])

    def read_product_info(self):
        self.send(0x00, 0x08, [])

    def read_recorder_params(self):
        self.read_params(0xAA, [0x05, 0x11, 0x20, 0x21, 0x30, 0x31, 0x32, 0x33])

    def read_linmaze_params(self):
        self.read_params(0xBB, [0x05, 0x10, 0x20, 0x21, 0x30, 0x31, 0x32, 0x33])

    def write_output(self, output, value):
        self.write_param(0x30+output-1, [int(value)])

    def write_analog(self, value):
        self.write_param(0x40, list(struct.pack('f', value)))

    def ping(self):
        data = sample(range(0, 255), 5)
        self.ping_time = time()
        self.send(0x00, 0x00, data)
        print('Ping!', data)

    def check_app(self):
        self.send(0x00, 0x05, [])

    def set_LED(self, state):
        self.send(0xFF, 0x12, [state])

    def reset(self):
        self.send(0x00, 0xF0, [])

    def reset_time(self):
        self.write_param(0x05, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    def reset_position(self):
        self.write_param(0x10, [0x00, 0x00, 0x00, 0x00])

    def read_param(self, param):
        self.send(param, 0x0B, [param])

    def read_params(self, msn, params):
        self.send(msn, 0x0B, params)

    def write_param(self, param, payload):
        self.send(param, 0x0C, [param]+payload)

    def send(self, msn, cmd, payload):
        plen = len(payload)
        filler = [0] * (65-plen-8)
        full = [0x0] + self.target + self.source + \
            [msn, cmd, plen] + payload + filler
        try:
            self.report.set_raw_data(full)
            self.report.send()
        except hid.helpers.HIDError as hid_error:
            # print('HID ERROR', hid_error)
            self.transmitter.emit_device_error(hid_error)

        # print('Sent:',[hex(byte) for byte in full])

        # print('Sent')
        # print('Target', self.target)
        # print('Source', self.source)
        # print('MSN', msn)
        # print('CMD', cmd)
        # print('PLen', plen)
        # print('Payload', payload)
        # print()

    def data_handler(self, data):
        target = data[1:3]
        source = data[3:5]
        if target == self.source and source == self.target:
            msn = data[5]
            cmd = data[6]
            plen = data[7]
            payload = data[8:8+plen]

            if cmd == 0x00:
                if self.ping_time is None:
                    print('Communication error: Received a pong but ping was never sent.')
                else:
                    delay = time()-self.ping_time
                print('Pong!', payload)
                print('Delay:', delay, 'sec\n')

            if cmd == 0x01:
                if self.verbose:
                    print(Gramophone.parameters[msn].name, 'OK!')

            if cmd == 0x02:
                print(Gramophone.parameters[msn].name, 'failed.',
                      self.error_codes[payload[0]])

            if cmd == 0x04:
                self.firmware_release = payload[0]
                self.firmware_sub = payload[1]
                self.firmware_build = int.from_bytes(
                    payload[2:4], 'little', signed=False)
                self.firmware_year = int.from_bytes(
                    payload[4:6], 'little', signed=False)
                self.firmware_month = payload[6]
                self.firmware_day = payload[7]
                self.firmware_hour = payload[8]
                self.firmware_minute = payload[9]
                self.firmware_second = payload[10]

                if self.verbose:
                    print('Firmware version')
                    print('Relase:', str(self.firmware_release) +
                          '.'+str(self.firmware_sub))
                    print('Build:', self.firmware_build)
                    print('Date:', str(self.firmware_year)+'-' +
                          str(self.firmware_month)+'-'+str(self.firmware_day))
                    print('Time', str(self.firmware_hour)+':' +
                          str(self.firmware_minute)+':'+str(self.firmware_second))
                    print()

            if cmd == 0x05:
                if payload[0] == 0x00:
                    if self.verbose:
                        print('CheckApp: IAP \n')
                    self.app_state = 'IAP'
                if payload[0] == 0x01:
                    if self.verbose:
                        print('CheckApp: Application \n')
                    self.app_state = 'App'

            if cmd == 0x08:
                self.product_name = ''.join(
                    [chr(byte) for byte in payload[0:18] if byte != 0x00])
                self.product_revision = ''.join(
                    [chr(byte) for byte in payload[18:24]])
                self.product_serial = int.from_bytes(
                    payload[24:28], 'little', signed=False)
                self.product_year = int.from_bytes(
                    payload[28:30], 'little', signed=False)
                self.product_month = int.from_bytes(
                    payload[30:31], 'little', signed=False)
                self.product_day = int.from_bytes(
                    payload[31:32], 'little', signed=False)

                if self.verbose:
                    print('Product Info')
                    print('Name:', self.product_name)
                    print('Revision:', self.product_revision)
                    print('Serial', hex(self.product_serial))
                    print('Production:', str(self.product_year)+'-' +
                          str(self.product_month)+'-'+str(self.product_day))
                    print()

            if cmd == 0x0B:
                val = None
                if payload is not None:
                    val = Gramophone.decode_payload(
                        Gramophone.parameters[msn].type, bytes(payload))
                if self.verbose:
                    print('Read:', Gramophone.parameters[msn].info,
                          'Value:', val)

                if Gramophone.parameters[msn].name == 'ENCVEL':
                    self.transmitter.emit_velocity(val)
                    self.last_velocity = val
                if Gramophone.parameters[msn].name == 'ENCPOS':
                    self.transmitter.emit_position(val)
                    self.last_position = val
                if Gramophone.parameters[msn].name == 'SENSORS':
                    self.sensor_values['VSEN3V3'] = val[0]
                    self.sensor_values['VSEN5V'] = val[1]
                    self.sensor_values['TSENMCU'] = val[2]
                    self.sensor_values['TSENEXT'] = val[3]
                if Gramophone.parameters[msn].name == 'DI':
                    self.transmitter.emit_inputs(val)
                    self.last_in_1 = val[0]
                    self.last_in_2 = val[1]
                if Gramophone.parameters[msn].name == 'DO':
                    self.last_out_1 = val[0]
                    self.last_out_2 = val[1]
                    self.last_out_3 = val[2]
                    self.last_out_4 = val[3]
                if Gramophone.parameters[msn].name == 'REC':
                    self.transmitter.emit_recorder(val)
                    self.last_time = val[0]
                    self.last_velocity = val[1]
                    self.last_in_1 = val[2]
                    self.last_in_2 = val[3]
                    self.last_out_1 = val[4]
                    self.last_out_2 = val[5]
                    self.last_out_3 = val[6]
                    self.last_out_4 = val[7]
                if Gramophone.parameters[msn].name == 'LINM':
                    # self.transmitter.emit_recorder(val)
                    self.last_time = val[0]
                    self.last_position = val[1]
                    self.last_in_1 = val[2]
                    self.last_in_2 = val[3]
                    self.last_out_1 = val[4]
                    self.last_out_2 = val[5]
                    self.last_out_3 = val[6]
                    self.last_out_4 = val[7]

            if cmd not in [0x00, 0x01, 0x02, 0x04, 0x05, 0x08, 0x0B]:
                print('CMD', hex(cmd))
                print('plen', plen)
                print('payload', payload)

    @background
    def start_burst(self, port, on_time, pause_time):
        self.bursting[port] = True
        while self.bursting[port]:
            self.write_output(port, 1)
            sleep(on_time)
            self.write_output(port, 0)
            sleep(pause_time)

    def stop_burst(self, port):
        self.bursting[port] = False

    def start_reader(self, name, param, freq):
        command = {'position': self.read_position,
                   'velocity': self.read_velocity,
                   'time': self.read_time,
                   'inputs': self.read_inputs,
                   'recorder': self.read_recorder_params
                   }[param]
        reader = Reader(name, command, freq)
        thread = QThread()
        # thread.setObjectName('thread_' + str(idx))
        self.readers.append((thread, reader))
        reader.moveToThread(thread)

        thread.started.connect(reader.read)
        thread.start()

    def stop_reader(self, name=None):
        if self.readers:
            for thread, reader in self.readers:
                if name is None or reader.name == name:
                    reader.abort()
                    thread.quit()
                    thread.wait()
