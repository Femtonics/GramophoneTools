from pywinusb import hid
from time import sleep, time
from random import randint, sample
import struct

from PyQt5.QtCore import QObject, pyqtSignal


class Transmitter(QObject):
    velocity_signal = pyqtSignal(float)

    def emit_velocity(self, vel):
        self.velocity_signal.emit(vel)


class Gramophone(hid.HidDevice):
    error_codes = {0x00: 'PACKET_FAIL_UNKNOWNCMD',
                   0x01: 'PACKET_FAIL_INVALIDCMDSYNTAX',
                   0x04: 'PACKET_FAIL_INVALIDPARAMSYNTAX',
                   0x05: 'PACKET_FAIL_RANGEERROR',
                   0x06: 'PACKET_FAIL_PARAMNOTFOUND',
                   0x07: 'PACKET_FAIL_VALIDFAIL',
                   0x08: 'PACKET_FAIL_ACCESSVIOLATION'}

    def __init__(self, verbose=False):
        dev_filter = hid.HidDeviceFilter(vendor_id=0x0483, product_id=0x5750)
        devices = dev_filter.get_devices()
        if devices:
            dev = devices[0]
        super().__init__(dev.device_path, dev.parent_instance_id, dev.instance_id)

        self.verbose = verbose

        self.report = None
        self.set_raw_data_handler(self.data_handler)

        self.transmitter = Transmitter()

        self.target = [0x0, 0x2]
        self.source = [0x72, 0xfd]

        self.ping_time = None
        self.app_state = 'Unknown'
        self.msn = 0

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

    def close(self):
        """ Disconnect from this device. """
        self.report = None
        super().close()

    @staticmethod
    def decode_param(param_id, payload):
        result = {'type': None,
                  'description': None,
                  'value': None}

        if payload is not None:
            payload = bytes(payload)
        else:
            payload = bytes([0, 0, 0, 0])

        if param_id == 0x01:
            result['type'] = 'VSEN3V3'
            result['description'] = 'Voltage on 3.3V rail.'
            result['value'] = struct.unpack('f', payload)[0]
        if param_id == 0x02:
            result['type'] = 'VSEN5V'
            result['description'] = 'Voltage on 5V rail.'
            result['value'] = struct.unpack('f', payload)[0]
        if param_id == 0x03:
            result['type'] = 'TSENMCU'
            result['description'] = 'Internal teperature of the MCU.'
            result['value'] = struct.unpack('f', payload)[0]
        if param_id == 0x04:
            result['type'] = 'TSENEXT'
            result['description'] = 'External temperature sensor on the board.'
            result['value'] = struct.unpack('f', payload)[0]

        if param_id == 0x10:
            result['type'] = 'ENCPOS'
            result['description'] = 'Encoder position.'
            result['value'] = int.from_bytes(payload, 'little', signed=True)
        if param_id == 0x11:
            result['type'] = 'ENCVEL'
            result['description'] = 'Encoder velocity.'
            result['value'] = struct.unpack('f', payload[0:4])[
                0]*float(payload[4])
        if param_id == 0x12:
            result['type'] = 'ENCVELWIN'
            result['description'] = 'Encoder velocity window size.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)
        if param_id == 0x13:
            result['type'] = 'ENCHOME'
            result['description'] = 'Encoder homing.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)
        if param_id == 0x14:
            result['type'] = 'ENCHOMEPOS'
            result['description'] = 'Encoder home position.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)

        if param_id == 0x20:
            result['type'] = 'DI-1'
            result['description'] = 'Digital input 1.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)
        if param_id == 0x21:
            result['type'] = 'DI-2'
            result['description'] = 'Digital input 2.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)
        if param_id == 0x25:
            result['type'] = 'DI'
            result['description'] = 'Digital inputs.'
            result['value'] = list(payload)

        if param_id == 0x30:
            result['type'] = 'DO-1'
            result['description'] = 'Digital output 1.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)
        if param_id == 0x31:
            result['type'] = 'DO-2'
            result['description'] = 'Digital output 2.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)
        if param_id == 0x32:
            result['type'] = 'DO-3'
            result['description'] = 'Digital output 3.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)
        if param_id == 0x33:
            result['type'] = 'DO-4'
            result['description'] = 'Digital output 4.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)
        if param_id == 0x35:
            result['type'] = 'DO'
            result['description'] = 'Digital outputs.'
            result['value'] = list(payload)

        if param_id == 0x40:
            result['type'] = 'AO'
            result['description'] = 'Analogue output.'
            result['value'] = struct.unpack('f', payload)[0]

        if param_id == 0xFF:
            result['type'] = 'LED'
            result['description'] = 'LED state changed.'
            result['value'] = int.from_bytes(payload, 'little', signed=False)

        return result

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

    def read_param(self, param):
        self.send(param, 0x0B, [param])

    def read_params(self, msn, params):
        self.send(msn, 0x0B, params)

    def write_param(self, param, payload):
        if param == 0x40:
            payload = list(struct.pack('f', payload[0]))
        self.send(param, 0x0C, [param]+payload)

    def send(self, msn, cmd, payload):
        plen = len(payload)
        filler = [0] * (65-plen-8)
        full = [0x0] + self.target + self.source + \
            [msn, cmd, plen] + payload + filler
        self.report.set_raw_data(full)
        self.report.send()

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
        msn = data[5]
        cmd = data[6]
        plen = data[7]
        payload = data[8:8+plen]

        if cmd == 0x00:
            delay = time()-self.ping_time
            print('Pong!', payload)
            print('Delay:', delay, 'sec\n')

        if cmd == 0x01:
            if self.verbose:
                param_type = Gramophone.decode_param(msn, None)['type']
                print(param_type, 'OK!')

        if cmd == 0x02:
            param_type = Gramophone.decode_param(msn, None)['type']
            err = payload[0]
            print(param_type, 'failed', self.error_codes[err])

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
            self.product_serial = hex(int.from_bytes(
                payload[24:28], 'little', signed=False))
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
                print('Serial', self.product_serial)
                print('Production:', str(self.product_year)+'-' +
                      str(self.product_month)+'-'+str(self.product_day))
                print()

        if cmd == 0x0B:
            parameter = Gramophone.decode_param(msn, payload)
            if self.verbose:
                print('Parameter read', parameter)
            if parameter['type'] == 'ENCVEL':
                self.transmitter.emit_velocity(parameter['value'])

        if cmd not in [0x00, 0x01, 0x02, 0x04, 0x05, 0x08, 0x0B]:
            print('CMD', hex(cmd))
            print('plen', plen)
            print('payload', payload)
