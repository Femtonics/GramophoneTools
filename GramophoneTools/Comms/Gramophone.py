import struct
from collections import namedtuple
from random import randint, sample
from threading import Thread
from time import sleep, time

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from pywinusb import hid


class Transmitter(QObject):
    velocity_signal = pyqtSignal(float)
    position_signal = pyqtSignal(int)

    def emit_velocity(self, vel):
        self.velocity_signal.emit(vel)

    def emit_position(self, pos):
        self.position_signal.emit(pos)


class Reader(QObject):
    def __init__(self, name, read_func, frequency):
        super().__init__()
        self.name = name
        self.read_func = read_func
        self.reading = None
        self.frequency = frequency

    @pyqtSlot()
    def read(self):
        self.reading = True
        while self.reading:
            self.read_func()
            sleep(1/self.frequency)

    def abort(self):
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
                  0x10: Parameter('ENCPOS', 'Encoder position.', 'int32'),
                  0x11: Parameter('ENCVEL', 'Encoder velocity.', 'vel_struct'),
                  0x12: Parameter('ENCVELWIN', 'Encoder velocity window size.', 'uint16'),
                  0x13: Parameter('ENCHOME', 'Encoder homing.', 'uint8'),
                  0x14: Parameter('ENCHOMEPOS', 'Encoder home position.', 'int32'),
                  0x20: Parameter('DI-1', 'Digital input 1.', 'uint8'),
                  0x21: Parameter('DI-2', 'Digital input 2.', 'uint8'),
                  0x25: Parameter('DI', 'Digital inputs.', 'list'),
                  0x30: Parameter('DO-1', 'Digital output 1.', 'uint8'),
                  0x31: Parameter('DO-2', 'Digital output 2.', 'uint8'),
                  0x32: Parameter('DO-3', 'Digital output 3.', 'uint8'),
                  0x33: Parameter('DO-4', 'Digital output 4.', 'uint8'),
                  0x35: Parameter('DO', 'Digital outputs.', 'list'),
                  0x40: Parameter('AO', 'Analogue output.', 'float'),
                  0xFF: Parameter('LED', 'LED state changed', 'uint8')}

    @classmethod
    def find_devices(cls):
        dev_filter = hid.HidDeviceFilter(vendor_id=0x0483, product_id=0x5750)
        devices = []
        for dev in dev_filter.get_devices():
            gram = cls(dev, verbose=True)
            gram.open()
            for _ in range(5):
                gram.read_product_info()
                sleep(0.1)
                if gram.product_name == 'GRAMO-01':
                    devices.append(gram)
                    break
            gram.close()
        return devices

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
    def decode_payload(val_type, payload):
        if val_type == 'float':
            return struct.unpack('f', payload)[0]
        if val_type == 'int32':
            return int.from_bytes(payload, 'little', signed=True)
        if val_type in ['uint8', 'uint16']:
            return int.from_bytes(payload, 'little', signed=False)
        if val_type == 'vel_struct':
            return struct.unpack('f', payload[0:4])[0]*float(payload[4])
        if val_type == 'list':
            return list(payload)

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
        if target == self.source and source == self.target:
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
                if Gramophone.parameters[msn].name == 'ENCPOS':
                    self.transmitter.emit_position(val)

            if cmd not in [0x00, 0x01, 0x02, 0x04, 0x05, 0x08, 0x0B]:
                print('CMD', hex(cmd))
                print('plen', plen)
                print('payload', payload)

    def start_reader(self, name, param, freq):
        command = {'position': self.read_position,
                   'velocity': self.read_velocity,
                   }[param]
        reader = Reader(name, command, freq)
        thread = QThread()
        # thread.setObjectName('thread_' + str(idx))
        self.readers.append((thread, reader))
        reader.moveToThread(thread)

        thread.started.connect(reader.read)
        thread.start()

    def stop_reader(self, name):
        for thread, reader in self.readers:
            if reader.name == name:
                reader.abort()
                thread.quit()
                thread.wait()
