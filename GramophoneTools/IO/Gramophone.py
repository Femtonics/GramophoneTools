from pywinusb import hid
from time import sleep, time
from random import randint, sample


class Gramophone(hid.HidDevice):
    error_codes = {0x00: 'PACKET_FAIL_UNKNOWNCMD',
                   0x01: 'PACKET_FAIL_INVALIDCMDSYNTAX',
                   0x04: 'PACKET_FAIL_INVALIDPARAMSYNTAX',
                   0x05: 'PACKET_FAIL_RANGEERROR',
                   0x06: 'PACKET_FAIL_PARAMNOTFOUND',
                   0x07: 'PACKET_FAIL_VALIDFAIL',
                   0x08: 'PACKET_FAIL_ACCESSVIOLATION'}

    def __init__(self):
        dev_filter = hid.HidDeviceFilter(vendor_id=0x0483, product_id=0x5750)
        devices = dev_filter.get_devices()
        if devices:
            dev = devices[0]
        super().__init__(dev.device_path, dev.parent_instance_id, dev.instance_id)

        self.report = None
        self.set_raw_data_handler(self.data_handler)

        self.target = [0x0, 0x2]
        self.source = [0x72, 0xfd]

        self.ping_time = None
        self.app_state = 'Unknown'
        self.msn = 0

    def open(self):
        super().open()
        reports = self.find_output_reports()
        self.report = reports[0]
        self.check_app()
        sleep(0.1)
        if self.app_state == 'IAP':
            print('Device in IAP state. Resetting...')
            self.reset()
            sleep(0.1)
        else:
            self.set_LED(1)

    def close(self):
        self.set_LED(0)
        self.report = None
        super().close()

    def ping(self):
        data = sample(range(0, 255), 5)
        self.ping_time = time()
        self.send(0, data)
        print('Ping!', data)

    def check_app(self):
        self.send(0x05, [])

    def get_firmware_version(self):
        self.send(0x04, [])

    def get_product_info(self):
        self.send(0x08, [])

    def set_LED(self, state):
        self.send(0x12, [state])

    def reset(self):
        self.send(0xF0, [])

    def read_param(self, param):
        self.send(0x0B, [param])

    def write_param(self, param, payload):
        self.send(0x0C, [param]+payload)

    def send(self, cmd, payload):
        plen = len(payload)
        filler = [0] * (65-plen-8)
        full = [0x0] + self.target + self.source + \
            [self.msn, cmd, plen] + payload + filler
        self.report.set_raw_data(full)
        self.report.send()
        self.msn += 1
        self.msn %= 256
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
            print('OK')

        if cmd == 0x02:
            err = payload[0]
            print('Failed command', self.error_codes[err])

        if cmd == 0x04:
            release = payload[0]
            sub = payload[1]
            build = int.from_bytes(payload[2:4], 'little', signed=False)
            year = int.from_bytes(payload[4:6], 'little', signed=False)
            month = payload[6]
            day = payload[7]
            hour = payload[8]
            minute = payload[9]
            second = payload[10]

            print('Firmware version')
            print('Relase:', str(release)+'.'+str(sub))
            print('Build:', build)
            print('Date:', str(year)+'-'+str(month)+'-'+str(day))
            print('Time', str(hour)+':'+str(minute)+':'+str(second))
            print()

        if cmd == 0x05:
            if payload[0] == 0x00:
                print('CheckApp: IAP \n')
                self.app_state = 'IAP'
            if payload[0] == 0x01:
                print('CheckApp: Application \n')
                self.app_state = 'App'

        if cmd == 0x08:
            name = [chr(byte) for byte in payload[0:18] if byte != 0x00]
            name_str = ''.join(name)

            revision = [chr(byte) for byte in payload[18:24]]
            revision_str = ''.join(revision)

            serial = hex(int.from_bytes(
                payload[24:28], 'little', signed=False))
            year = int.from_bytes(payload[28:30], 'little', signed=False)
            month = int.from_bytes(payload[30:31], 'little', signed=False)
            day = int.from_bytes(payload[31:32], 'little', signed=False)

            print('Product Info')
            print('Name:', name_str)
            print('Revision:', revision_str)
            print('Serial', serial)
            print('Production:', str(year)+'-'+str(month)+'-'+str(day))
            print()

        if cmd == 0x0B:
            print('Parameter read')
            print('Value', int.from_bytes(payload, 'little', signed=False))

        if cmd not in [0x00, 0x01, 0x02, 0x04, 0x05, 0x08, 0x0B]:
            print('CMD', hex(cmd))
            print('plen', plen)
            print('payload', payload)

        # print('Received:',[hex(d) for d in data])


if __name__ == '__main__':
    gram = Gramophone()
    gram.open()

    sleep(1)
    gram.ping()
    # print()

    gram.get_product_info()
    gram.get_firmware_version()
    print('App state:', gram.app_state)
    # gram.check_app()
    # gram.reset()
    # print()

    # gram.write_param(0xD0, [1,2,3,4])
    # gram.read_param(0xD0)

    # for T in range(100):
    #     gram.read_param(0x10)
    #     sleep(0.5)

    for I in range(10):
        gram.write_param(0x30, [1])
        sleep(0.1)
        gram.write_param(0x30, [0])
        sleep(0.1)

    sleep(1)
    gram.close()
