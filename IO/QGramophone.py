""" A QT based interface for communicationg with Femto-Gramophone """
import time
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo


class QGramophone(QSerialPort):
    """ Gramophone object for serial communication with the device.
        Emits read values as QT signals. """

    time_sig = pyqtSignal(int)
    vel_sig = pyqtSignal(int)
    rec_sig = pyqtSignal(int)
    all_sig = pyqtSignal(int, int, int)

    def __init__(self):
        super().__init__()
        self.setBaudRate(QSerialPort.Baud115200)
        self.setDataBits(QSerialPort.Data8)
        self.setParity(QSerialPort.NoParity)
        self.setStopBits(QSerialPort.OneStop)

        self.readyRead.connect(self.read_bytes)

    def open(self, qport):
        """ Starts the communication with the device on the given port.
            Expects the port as a QSerialPortInfo object.  """

        self.setPort(qport)
        return super().open(QSerialPort.ReadWrite)

    @pyqtSlot()
    def read_bytes(self):
        """ A function automatically called when there is serial data
            available for reading. Emits the decoded velocity data as
            pyqtSignals """
        time.sleep(0.001)
        line = bytes(self.readLine())
        time.sleep(0.001)
        try:
            t, v, r = line.decode()[:-2].split(' ')
            t, v, r = int(t), int(v), int(r)
            self.time_sig.emit(t)
            self.vel_sig.emit(v)
            self.rec_sig.emit(r)
            self.all_sig.emit(t, v, r)
        except (AttributeError, TypeError, ValueError) as error:
            print('Gram. Error: ', type(error), error)
            print(line, '\n')

    @staticmethod
    def find_grams(verbose=False):
        """ Returns a list of QSerialPortInfo objects that are Gramophones. """

        ports = [port
                 for port in QSerialPortInfo.availablePorts()
                 if port.productIdentifier() in [32847, 67]]

        if verbose:
            for port in ports:
                print(port.portName())
                print(port.manufacturer())
                print('PID', port.productIdentifier())
                print('VID', port.vendorIdentifier())
                print()
        return ports


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow
    P = QGramophone.find_grams()[0]
    gram = QGramophone()
    gram.all_sig.connect(print)
    gram.errorOccurred.connect(print)
    gram.open(P)

    APP = QApplication(sys.argv)
    WIN = QMainWindow()
    WIN.show()
    sys.exit(APP.exec_())

    gram.close()
