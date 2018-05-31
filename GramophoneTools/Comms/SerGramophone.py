''' Used for handleing Gramophone hardware '''

import threading
from time import sleep
import serial
import serial.tools.list_ports
import numpy as np


class Port(object):
    ''' An output of the parent Gramophone '''

    def __init__(self, parent, letter):
        self.parent = parent
        self.letter = letter
        self.state = 0
        self.bursting = False
        # self.turn_off()

    def turn_on(self):
        ''' Truns on the port '''
        message = self.letter.upper()
        self.parent.write_data(message.encode('utf-8'))
        self.state = 1

    def turn_off(self):
        ''' Truns off the port '''
        message = self.letter.lower()
        self.parent.write_data(message.encode('utf-8'))
        self.state = 0

    def pulse_thread(self, length):
        ''' Runs in the background and pulses an output once '''
        self.turn_on()
        sleep(length)
        self.turn_off()

    def pulse(self, length):
        ''' Starts pulsing on a given port '''
        pthread = threading.Thread(target=self.pulse_thread, args=[length, ])
        pthread.start()

    def burst_thread(self, length, pause):
        ''' Thread for countinous pulsing with a pause '''
        while self.bursting:
            self.pulse_thread(length)
            sleep(pause)

    def burst_on(self, length, pause):
        ''' Countinous pulsing with a pause '''
        if self.bursting:
            self.burst_off()
        bthread = threading.Thread(
            target=self.burst_thread, args=[length, pause])
        self.bursting = True
        bthread.start()

    def burst_off(self):
        ''' Stops bursting '''
        self.bursting = False
        self.turn_off()


class Gramophone(object):
    ''' An object that can connect to and read & write values of a Gramophone device '''

    def __init__(self):
        self.connected = False
        self.ser = None

        self.bcg_t = 0
        self.bcg_v = 0
        self.bcg_a = 0

        self.bcg_running = False
        self.v_list = []

        self.ports = {'A': Port(self, 'A'), 'B': Port(
            self, 'B'), 'C': Port(self, 'C')}

    @staticmethod
    def find_grams():
        ''' Retruns a list of Gramophone ports '''
        arduino_ports = [
            p.device
            for p in serial.tools.list_ports.comports()
            if p.serial_number == "A600HISAA" or p.pid == 32847 or p.pid == 67
        ]

        return arduino_ports

    def connect(self, port):
        ''' Connects to a Gramophone on the given COM port '''

        print('Connecting to Gramophone on port: ' + port)

        while self.ser is None:
            try:  # ...to connect to the gramophone
                self.ser = serial.Serial(port, 115200)
            except serial.SerialException as exception:
                print(exception)
                print("Error: Serial connection cannot be etablished. \
                    Device in use by an other process.")
                print("Retry in 5 seconds...\n")
                sleep(5)
            else:
                self.connected = True
                print("Serial connection established.\n")

    def autoconnect(self):
        ''' Connect to the first Gramophone found '''
        ports = self.find_grams()
        while not ports:
            print("Error: No Gramophone found. Please connect one.")
            print("Retry in 5 seconds...\n")
            sleep(5)
            ports = self.find_grams()
        if len(ports) > 1:
            print("Warning: Multiple Gramophone found - using the first")
        self.connect(ports[0])

    def disconnect(self):
        ''' Disconnects the Gramophone '''
        self.stop_burst()
        while any([port.state for port in list(self.ports.values())]):
            sleep(0.5)
        self.stop_bcg()
        sleep(0.5)
        self.ser.close()
        self.connected = False
        print("Disconnected from Gramophone.")

    def read_data(self):
        ''' Returns 3 values. Time, Velocity and Analog input in order '''
        try:
            string_read = self.ser.readline()
            string_read = string_read.decode(encoding='ascii')
            string_read = string_read.rstrip()
            g_time, g_vel, g_analog = string_read.split(" ")
            g_time, g_vel, g_analog = int(g_time), int(g_vel), int(g_analog)

        except serial.SerialException as exception:
            print(exception)
            print("Gramophone uplugged")
            # LOG
            self.connected = False
            return -1, 0, 0

        except (ValueError, UnicodeDecodeError) as exception:
            print(exception)
            print("Serial communication error")
            # LOG
            return -1, 0, 0

        else:
            return g_time, g_vel, g_analog

    def write_data(self, data):
        ''' Sends the given data to the connected Gramophone '''
        if self.connected:
            self.ser.write(data)
        else:
            print("Can't send data. No Gramophone connected.")

    def reset(self):
        ''' Sends a command that resets the Gramophone's internal clock '''
        self.write_data('R'.encode('utf-8'))

    def pulse(self, port, length):
        ''' Pulses the given port '''
        port = port.upper()
        self.ports[port].pulse(length)

    def start_burst(self, port, length, pause):
        ''' Starts bursting on the given port '''
        port = port.upper()
        self.ports[port].burst_on(length, pause)

    def stop_burst(self, port=None):
        ''' Starts bursting on the given port or all ports if non were given '''
        if port is None:
            # print("Stop bursting on all ports")
            for key in self.ports:
                self.ports[key].burst_off()
        else:
            port = port.upper()
            self.ports[port].burst_off()

    def bcg_read(self):
        ''' Keeps reading the values of the Gramophone '''
        while self.bcg_running:
            self.bcg_t, self.bcg_v, self.bcg_a = self.read_data()
            if self.bcg_t != -1:
                self.v_list.append(self.bcg_v)
            # sleep(0.001)

    def start_bcg(self):
        ''' Starts a loop in the background that reads the Gramophone
        values and updates the bcg_t, bcg_v and bcg_a values '''
        self.bcg_running = True
        self.v_list = []
        Gramophone_thread = threading.Thread(target=self.bcg_read)
        Gramophone_thread.start()

    def stop_bcg(self):
        ''' Stops the loop that reads values in the background '''
        self.bcg_running = False

    def get_mean_vel(self):
        ''' Returns the mean of velocities since the last time this command was used '''
        if self.v_list:
            vel = np.mean(self.v_list)
        else:
            vel = 0
        self.v_list = []
        return vel
