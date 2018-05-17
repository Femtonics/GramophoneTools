from pywinusb import hid
from time import time, sleep
from msvcrt import kbhit
from collections import deque
from statistics import mean

old_time = time()
etimes = deque([],1000)

def sample_handler(data):
    global old_time
    global etimes

    # print("Raw data: {0}".format(data))
    elapsed = time()-old_time
    etimes.append(elapsed)
    # print('\r', data[1], data[2], end='\r')
    enc_val = data[1] + data[2]*256 + data[3]*(256**2) + data[4]*(256**3)
    print(enc_val)
    old_time = time()

filter = hid.HidDeviceFilter(vendor_id = 0x16C0, product_id = 0x0486)
# filter = hid.HidDeviceFilter(vendor_id = 0x0483, product_id = 0x5750)

devices = filter.get_devices()

for dev in devices:
    print(dev)

if devices:
    device = devices[0]
    print("success")

device.open()
device.set_raw_data_handler(sample_handler)

while not kbhit() and device.is_plugged():
    #just keep the device opened to receive events
    sleep(0.5)

device.close()
