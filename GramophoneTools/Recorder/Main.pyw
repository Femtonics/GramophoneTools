""" Software made for recording velocity form a Femto-Gramophone
    in a triggered manner. Can be used in conjunction with two-photon
    microscoppes by Femtonics Inc. """

import os
import sys
import time
from collections import deque
from statistics import mean

import h5py
import matplotlib.pyplot as plt

from PyQt5 import QtCore
from PyQt5.uic import loadUiType
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMessageBox, QHeaderView, QFileDialog
from PyQt5.QtSerialPort import QSerialPort

from GramophoneTools.Recorder import GramLogging
from GramophoneTools.Comms.Gramophone import Gramophone

# GLOBALS
DIR = os.path.dirname(__file__)
sys.path.append(DIR)
ABOUT_WIN_BASE, ABOUT_WIN_UI = loadUiType(DIR+'\\about.ui')
LICENSE_WIN_BASE, LICENSE_WIN_UI = loadUiType(DIR+'\\license.ui')
MAIN_WIN_BASE, MAIN_WIN_UI = loadUiType(DIR+'\\main.ui')


class aboutWindow(ABOUT_WIN_BASE, ABOUT_WIN_UI):
    """ The window shown if the user clicks the About
        option in the Help menu. Displays basic info
        about the software.  """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.close_btn.clicked.connect(self.close)


class licenseWindow(LICENSE_WIN_BASE, LICENSE_WIN_UI):
    """ The window shown if the user clicks the License
        option in the Help menu. Displays the open source
        license the software is distributed under. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.close_btn.clicked.connect(self.close)


class pyGramWindow(MAIN_WIN_BASE, MAIN_WIN_UI):
    """ The main window of the Gramophone reader. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.about_win = aboutWindow()
        self.license_win = licenseWindow()
        self.extra_windows = []

        # Properties
        self.recording = False

        # Live plot
        self.graph.setBackground(None)
        self.graph.hideButtons()
        self.graph.setMouseEnabled(x=False, y=False)
        self.graph.showAxis(axis='bottom', show=False)
        # self.graph.setLabel(axis='bottom', text='Time')
        # self.graph.showLabel(axis='bottom', show=False)
        self.graph.showGrid(x=False, y=True, alpha=1)
        self.graph.disableAutoRange(axis='y')
        self.graph.setYRange(-70000, 70000, padding=0, update=False)
        self.reset_graph()

        # Make initial file
        self.new_file()
        self.current_record = None

        # Buttons
        self.connect_btn.clicked.connect(self.connect_btn_cb)
        self.refresh_btn.clicked.connect(self.refresh_gram_list)
        self.plot_btn.clicked.connect(self.plot_btn_cb)
        self.select_all_btn.clicked.connect(self.records_table.selectAll)
        self.delete_btn.clicked.connect(self.delete_btn_cb)

        # Menu actions
        self.actionNew_File.triggered.connect(self.new_file)
        self.actionNew_Window.triggered.connect(self.new_window)
        self.actionOpen.triggered.connect(self.open)
        self.actionSave.triggered.connect(self.save)
        self.actionSave_As.triggered.connect(self.save_as)
        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.about)
        self.actionLicense.triggered.connect(self.license)
        self.actionGramophone_manual.triggered.connect(self.manual)

        # Timers
        self.timer_timer = 0
        self.graph_timer = 0

        # Gramophone
        devs = Gramophone.find_devices()
        self.gram = Gramophone(devs[0], verbose=True)
        self.gram.open()
        self.gram.bcg_read()
        # self.gram.error_msg.connect(self.gramophone_error)
        # self.gram.transmitter.time_sig.connect(self.update_timer)
        self.gram.transmitter.velocity_signal.connect(self.update_graph)
        # self.gram.transmitter.rec_sig.connect(self.update_rec_state)
        # self.gram.transmitter.errorOccurred.connect(self.gramophone_error)

        # Initialize GUI
        self.refresh_gram_list()

        # Developer options
        self.menuDEV.menuAction().setVisible(False)
        self.DEV_reset_gram_timer.triggered.connect(self.reset_gram_timer)
        self.DEV_make_dummy.triggered.connect(self.make_dummy)

    @pyqtSlot()
    def log_changed(self):
        """ Calll this function when the velocity log is modified
            and it should be saved. """
        self.setWindowModified(True)

    def update_title(self):
        ''' Updates the tile of the window with the name of the
            current file and a * character if there are unsaved
            changes made to said file. Called after the current
            file is changed or saved. '''
        if self.log.filename is not None:
            self.setWindowTitle('Gramophone Recorder - ' +
                                os.path.basename(self.log.filename) + '[*]')

    def new_file(self):
        """ Creates a new blank velocity log file and sets it
            as the current working file. """
        response = self.save_warning()
        if response != 'cancel':
            if response == 'save':
                self.save()

            self.counter_box.setValue(1)

            # Table of recordings
            self.log = GramLogging.VelocityLog(None)
            self.log_model = VelLogModel(self.log)
            self.log_model.dataChanged.connect(self.log_changed)
            self.log_model.rowsInserted.connect(self.update_table_size)
            self.records_table.setModel(self.log_model)
            self.records_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.update_table_size()
            # self.records_table.horizontalHeader().setResizeMode(QHeaderView.Fixed) #old
            # self.records_table.resizeColumnsToContents()
            self.setWindowModified(False)

    def new_window(self):
        """ Opens a new instance of the Gramophone recorder.
            New windows can be used for simultanious recording
            of an other Gramophone device. """
        os.startfile(DIR+"\\pyGram.pyw")

    def open(self):
        """ Opens a velocity log from file and sets it as the
            current working file. """
        self.new_file()
        if self.select_file(mode='open'):
            log_file = h5py.File(self.log.filename, "r")
            for key in list(log_file.keys()):
                loaded_record = GramLogging.FileRecord(key)
                self.log_model.add_record(loaded_record)

            log_file.close()
            self.update_table_size()

    def save(self):
        ''' Saves the currently used log file. Returns
            True if the file is saved or False if saving
            was cancelled '''
        if self.log.filename is None:
            if self.select_file():
                return self.save()
            else:
                return False
        else:
            self.log.save()
            self.setWindowModified(False)
            self.update_title()
            return True

    def save_as(self):
        ''' Same as save, but shows a file selection dialog
            to save to an other file. '''
        if self.select_file():
            self.save()

    def select_file(self, mode='save'):
        ''' Displays a file selection dialog for velocity
            log files. Mode can be 'save' or 'open'. '''
        options = QFileDialog.Options()
        fileformat = "pyGram logs (*.vlg)"

        if mode == 'save':
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save velocity log", "", fileformat, options=options)
        if mode == 'open':
            filename, _ = QFileDialog.getOpenFileName(
                self, "Open velocity log", "", fileformat, options=options)
        if filename:
            self.log.filename = filename
            self.update_title()
            return True
        else:
            return False

    def about(self):
        """ Displays the About window. """
        self.about_win = aboutWindow()
        self.about_win.show()

    def license(self):
        """ Displays the License window. """
        self.license_win = licenseWindow()
        self.license_win.show()

    def manual(self):
        """ Opens the Gramophone User Guide in the default
            pdf reader. """
        os.startfile(DIR+"\\doc\\Gramophone User Guide.pdf")

    def reset_graph(self):
        """ Resets the live velocity plot to its starting
            state ie. erases the plot if there is already
            something on it. """
        self.graph.clear()
        self.graph_time = deque([], maxlen=367)
        self.graph_vel = deque([], maxlen=367)
        self.vel_window = deque([], maxlen=10)
        self.curve = self.graph.plot(
            self.graph_time, self.graph_vel, pen='k', antialias=True)
        #, downsample=1, downsampleMethod='mean'
        ax_y = self.graph.getAxis('left')
        ax_y.setTickSpacing(major=10, minor=10)

    @pyqtSlot()
    def connect_btn_cb(self):
        """ Callback for the connect button. """
        if self.gram.isOpen():
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """ Connects to the currently selected Gramophone. """
        # Connect to currently selected Gramophone
        self.gram.port_name = self.gram_dropdown.currentData(0)
        port = [gram
                for gram in self.gram_list
                if gram.portName() == self.gram.port_name][0]
        self.gram.open(port)
        self.update_conn_state()

    def disconnect(self):
        """ Disconnects the currently connected Gramophone. """
        # Disconnect form Gramophone
        self.gram.close()
        self.reset_graph()
        self.update_timer(0)
        self.update_conn_state()

    @pyqtSlot()
    def refresh_gram_list(self):
        """ Refreshes the list of available Gramophones. """
        self.gram_list = Gramophone.find_devices()
        # port_names = [gram.portName() for gram in self.gram_list]
        port_names = [str(device) for device in self.gram_list]
        if self.gram_list:
            self.connect_btn.setProperty("enabled", True)
            self.gram_dropdown.clear()
            self.gram_dropdown.addItems(port_names)
        else:
            self.gram_dropdown.clear()
            self.connect_btn.setProperty("enabled", False)

    @pyqtSlot()
    def plot_btn_cb(self):
        """ Callback for the Plot button. """
        self.log_model.plot_record(self.selected_rows)

    @pyqtSlot()
    def delete_btn_cb(self):
        """ Callback for the Delete button. """
        if self.delete_warning(len(self.selected_rows)) == 'delete':
            while self.selected_rows:
                self.log_model.removeRows(self.selected_rows[0], 1)
        else:
            pass

    @property
    def selected_rows(self):
        """ A property that holds a list of the selected rows of
            the current velocity log. """
        return [index.row()
                for index
                in self.records_table.selectionModel().selectedRows()]

    def update_conn_state(self):
        """ Updates the GUI depending on wheter the software is
            currently connected to a Gramophone. """
        if self.gram.isOpen():
            # Change GUI for connected state
            self.gram_dropdown.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.connect_btn.setProperty("text", "Disconnect")

            self.statusbar.showMessage('Connected to Gramophone on port: '
                                       + str(self.gram.port_name), 3000)
        else:
            # Change GUI for disconnected state
            self.gram_dropdown.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.connect_btn.setProperty("text", "Connect")
            self.refresh_gram_list()
            self.statusbar.showMessage('Disconnected from Gramophone on port: '
                                       + str(self.gram.port_name), 3000)

    @pyqtSlot(int)
    def update_timer(self, millis):
        """ Slot for the time_signal of the Gramophone. Updates the
            timer on the GUI. """
        self.timer_timer += 1
        if self.timer_timer > 300:
            seconds = int((millis / 1000) % 60)
            minutes = int((millis / (1000 * 60)) % 60)
            # hours=(millis/(1000*60*60))%24
            self.time_label.setText(str(minutes).zfill(
                2) + ':' + str(seconds).zfill(2))

            self.timer_timer = 0

    @pyqtSlot(float)
    def update_graph(self, velocity):
        ''' Slot for the vel_signal of the Gramophone. Shifts the
            graph to the right and appends with the value received. '''
        self.vel_window.append(velocity)
        self.graph_timer += 1
        if not bool(self.graph_timer % 10):
            self.graph_time.append(time.time())
            self.graph_vel.append(mean(self.vel_window))
            if self.recording:
                self.curve.setPen(color='r', width=2)
            else:
                self.curve.setPen(color='k', width=2)
                # self.curve.setShadowPen(color=0.5, width=3)

            self.curve.setData(x=list(self.graph_time), y=list(self.graph_vel))
            self.graph.setXRange(
                self.graph_time[-1] - 10, self.graph_time[-1])  # last 10 seconds

    @pyqtSlot(int)
    def update_rec_state(self, rec_state):
        """ Slot for the rec_signal of the Grmaophone. Updates
            the state of recording and the GUI. """
        if self.recording != bool(rec_state):
            self.recording = bool(rec_state)
            if self.recording:
                self.current_record = GramLogging.MemoryRecord(
                    self.counter_box.value())
                self.current_record.start()
                self.gram.all_sig.connect(self.current_record.append)

                # Update GUI
                self.statusbar.showMessage('Recording started', 3000)
                self.connect_btn.setEnabled(False)
                self.counter_box.setEnabled(False)

            else:
                self.current_record.finish()
                # self.log_model.layoutChanged.emit()
                # currentRowCount = self.log_model.rowCount(self.log_model.parent)
                # self.log_model.insertRow(currentRowCount)
                # self.records_table.resizeColumnsToContents()
                # self.records_table.horizontalHeader().geometriesChanged().emit()
                self.gram.all_sig.disconnect(self.current_record.append)
                self.log_model.add_record(self.current_record)

                # Update GUI
                self.statusbar.showMessage('Recording finished', 3000)
                self.log_changed()
                self.update_table_size()
                self.connect_btn.setEnabled(True)
                self.counter_box.setEnabled(True)
                self.counter_box.stepUp()

    @pyqtSlot(QSerialPort.SerialPortError)
    def gramophone_error(self, error_code):
        """ Slot for the errorOccurred signal of the Gramophone. Displays
            a message box with the warning, disconnects if necessary. """
        if error_code == 2:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Connection error!")
            msg_box.setText("Cannot connect to Gramophone on port "
                            + self.gram.port_name)
            msg_box.setInformativeText('Device is no longer available'
                                       ' or in use by an other process.')
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setDefaultButton(QMessageBox.Ok)
            msg_box.exec()
        if error_code == 9:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Connection error!")
            msg_box.setText("The connection to the Gramophone was lost.")
            msg_box.setInformativeText('Please check cables.')
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setDefaultButton(QMessageBox.Ok)
            msg_box.exec()
        if error_code != 13:
            self.disconnect()

        print('ERROR:', error_code)
        self.update_conn_state()

    @pyqtSlot()
    def update_table_size(self):
        ''' Update all except last the row's width to fit content in
            the list of velocity recordings. '''
        for I in range(len(self.log_model.headers)-1):
            self.records_table.resizeColumnToContents(I)

    def record_warning(self):
        """ Displays a warning if the recording is in progress.
            Call it if the user tries to exit. """
        if self.recording:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Recording in progress")
            msg_box.setText("Recording is currently in progress.")
            msg_box.setInformativeText("Are you sure you want to exit?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Cancel)
            choice = msg_box.exec()
            if choice == QMessageBox.Yes:
                return 'ignore'
            if choice == QMessageBox.Cancel:
                return 'cancel'
        else:
            return 'safe'

    def save_warning(self):
        """ Displays a warning if there are unsaved changes to the log file.
            Call it if the user tries to exit. """
        if self.isWindowModified():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Unsaved changes")
            msg_box.setText("Do you want to save the changes"
                            "to this log before closing it?")
            msg_box.setInformativeText("If you don't save, "
                                       "your changes will be lost.")
            msg_box.setStandardButtons(
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Save)
            choice = msg_box.exec()
            if choice == QMessageBox.Save:
                return 'save'
            if choice == QMessageBox.Discard:
                return 'discard'
            if choice == QMessageBox.Cancel:
                return 'cancel'

    def delete_warning(self, count):
        """ Displays a message box to ask for confirmation. Call it
            if the user is trying to delete velocity records. """
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Delete records")
        msg_box.setText("Are you sure you want to delete the " +
                        str(count)+" selected record(s).")
        # msg_box.setInformativeText("")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        choice = msg_box.exec()
        if choice == QMessageBox.Yes:
            return 'delete'
        if choice == QMessageBox.Discard:
            return 'keep'

    def closeEvent(self, event):
        ''' The built in close event of QMainWindow. User is
            trying to close the program. Ignore the passed
            event if you want to stop the user from doing so. '''
        record_response = self.record_warning()

        if record_response == 'cancel':
            event.ignore()
        if record_response in ['ignore', 'safe']:
            save_response = self.save_warning()

            if save_response == 'save':
                saved = self.save()
                if not saved:
                    print('not saved')
                    event.ignore()
                else:
                    print('saved')
                    self.closeEvent(event)
            if save_response == 'cancel':
                event.ignore()
            if save_response in ['discard', 'safe']:
                pass

    def quit(self):
        """ Close all windows and disconnrect form the Gramohone.
            Call this right before exiting. """
        # sys.exit()
        self.about_win.close()
        self.license_win.close()
        self.gram.close()

    # Dev functions
    @pyqtSlot()
    def reset_gram_timer(self):
        """ Function only available for developers. Sends a Reset
            internal clock command to the Gramophone. """
        self.gram.write(b'R')

    @pyqtSlot()
    def make_dummy(self):
        """ Function only available for developers. Creates
            a dummy record in the current velocity log with
            randomized data. """
        dummy = GramLogging.DummyRecord()
        self.log_model.add_record(dummy)
        self.update_table_size()
        self.log_changed()


class VelLogModel(QAbstractTableModel):
    """ QT modell for velocity logs. Used to make an interface
        between the GUI's table view and the Velocity log object """

    def __init__(self, log, parent=None):
        super().__init__(parent)
        self.log = log
        # self.records = self.log.records
        self.headers = ['ID', 'Date', 'Start', 'Finish',
                        'Length', 'Mean velocity', 'Comment']

    def rowCount(self, parent):
        """ Return the number of rows to be displayed.
            one row for each recording. """
        return len(self.log.records)

    def columnCount(self, parent):
        ''' Return the number of columns to be displayed.
            One column for each header. '''
        return len(self.headers)

    def data(self, index, role):
        """ Called to receive information about a cell of the table. """
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return self.log.records[index.row()].rec_id
            if index.column() == 1:
                return self.log.records[index.row()].date_hr
            if index.column() == 2:
                return self.log.records[index.row()].start_time_hr
            if index.column() == 3:
                return self.log.records[index.row()].finish_time_hr
            if index.column() == 4:
                return self.log.records[index.row()].length_hr
            if index.column() == 5:
                return str(self.log.records[index.row()].mean_vel)[0:10]
            if index.column() == 6:
                return self.log.records[index.row()].comment

        if role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return self.log.records[index.row()].rec_id
            if index.column() == 6:
                return self.log.records[index.row()].comment

        if role == QtCore.Qt.SizeHintRole:
            if index.column() == 0:
                return QtCore.QSize(40, 30)
            if index.column() == 1:
                return QtCore.QSize(65, 30)
            if index.column() == 2:
                return QtCore.QSize(50, 30)
            if index.column() == 3:
                return QtCore.QSize(50, 30)
            if index.column() == 4:
                return QtCore.QSize(50, 30)
            if index.column() == 5:
                return QtCore.QSize(85, 30)
            if index.column() == 6:
                return QtCore.QSize(100, 30)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """ Called to set the data in a cell of the table. """
        if role == QtCore.Qt.EditRole:
            if index.column() == 0:
                self.log.records[index.row()].rec_id = value
                self.dataChanged.emit(index, index)
                return True
        if role == QtCore.Qt.EditRole:
            if index.column() == 6:
                self.log.records[index.row()].comment = value
                self.dataChanged.emit(index, index)
                return True
        else:
            return False

    def headerData(self, section, orientation, role):
        """ Returns the haeder data the GUI is asking for. """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.headers[section]
            if orientation == QtCore.Qt.Vertical:
                return section+1

    def flags(self, index):
        """ Returns flag to decide which cells are editable. """
        if index.column() in [0, 6]:  # List of editable columns
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def add_record(self, record):
        """ Adds the given Record object the the current velocity log. """
        record_count = len(self.log.records)
        self.beginInsertRows(QModelIndex(), record_count, record_count)
        self.log.records.append(record)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """ Removes 'count' number of rows starting at 'row' """
        self.beginRemoveRows(parent, row, row+count-1)
        self.log.records = self.log.records[:row] + \
            self.log.records[row+count:]
        self.endRemoveRows()

    def plot_record(self, selection):
        """ Plots the selected record(s) using Matplotlib. """
        plt.figure()
        selected_records = [self.log.records[row] for row in selection]
        for rec in selected_records:
            # print(rec.mean_vel)
            # print(rec.rec_id)
            plt.plot(rec.times[0::10], rec.velocities[0::10],
                     label=str(rec.rec_id)+' '+rec.comment)
            plt.xlabel('Time (ms)')
            plt.ylabel('Velocity (a.u.)')

        plt.legend()
        plt.show()


def main():
    APP = QApplication(sys.argv)
    WIN = pyGramWindow()
    # WIN.show_elements()
    WIN.show()
    sys.exit(APP.exec_())

if __name__ == '__main__':
    main()