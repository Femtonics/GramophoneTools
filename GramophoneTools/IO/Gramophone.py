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
        filter = hid.HidDeviceFilter(vendor_id=0x0483, product_id=0x5750)
        devices = filter.get_devices()
        if devices:
            dev = devices[0]
        super().__init__(dev.device_path, dev.parent_instance_id, dev.instance_id)

        self.report = None
        self.set_raw_data_handler(self.data_handler)

        self.target = [0x0, 0x2]
        self.source = [0x72, 0xfd]
        self.msn = randint(0, 255)

        self.ping_time = None

    def open(self):
        super().open()
        reports = self.find_output_reports()
        self.report = reports[0]

    def close(self):
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

    def write_param(self, param):
        self.send(0x0C, [param])

    def send(self, cmd, payload):
        plen = len(payload)
        filler = [0] * (65-plen-8)
        full = [0x0] + self.target + self.source + \
            [self.msn, cmd, plen] + payload + filler
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
            if payload[0] == 0x01:
                print('CheckApp: Application \n')

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
            print(payload)

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
    gram.check_app()
    # gram.reset()
    # print()

    print()

    while 1:
        gram.read_param(0xD0)

    # while 1:
    #     gram.set_LED(1)
    #     sleep(0.3)
    #     gram.set_LED(0)
    #     sleep(0.3)

    sleep(1)
    gram.close()
