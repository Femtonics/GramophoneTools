""" Module for logging Velocity data form the Gramophone into HDF5 files. """

import os.path
import time
from abc import ABC, abstractmethod

import h5py
import numpy as np
import xlsxwriter


class VelocityLog(object):
    """ A container object for velocity recordins. Handles
        saving records to HDF5 files. """

    def __init__(self):
        self.filename = None
        self.records = []
        self.deleted = []
        self.log_file = None

    @classmethod
    def from_file(cls, filename):
        loaded_log = cls()
        try:
            loaded_log.filename = filename
            loaded_log.log_file = h5py.File(loaded_log.filename, "a")
            for key in sorted(loaded_log.log_file.keys(), key=lambda key: loaded_log.log_file[key].attrs['start_time']):
                loaded_log.records.append(FileRecord(loaded_log.log_file[key]))
        except OSError as err:
            print(err)

        return loaded_log

    def open_log_file(self, filename, mode='a'):
        self.filename = filename
        self.log_file = h5py.File(self.filename, mode)

    def save(self):
        """ Saves all records from this log to file. """
        for rec_id, record in enumerate(self.records):
            print('Saved:', record)
            self.records[rec_id] = record.save(self.log_file)

        for record in self.deleted:
            if isinstance(record, FileRecord):
                del self.log_file[record.unique_id]
        self.deleted = []

    def close_log_file(self):
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None

    def xls_export(self, filename):
        if self.records:
            counter = 0
            workbook = xlsxwriter.Workbook(filename)
            data_sheet = workbook.add_worksheet('Data')
            metadata_sheet = workbook.add_worksheet('Metadata')
            for record in self.records:
                # Data sheet
                data_sheet.merge_range(0, counter, 0, counter+1, record.unique_id)

                comment = 'ID:{}\nDate: {}\nStart: {}\nFinish:{}\nLength: {}\nMean velocity: {}\nComment: {}'.format(
                    record.rec_id, record.date_hr, record.start_time_hr, record.finish_time_hr, record.length_hr, record.mean_vel, record.comment
                )
                data_sheet.write_comment(0,counter, comment, {'x_scale': 1.5, 'y_scale': 1.5})
                data_sheet.write(1,counter, 'time')
                data_sheet.write(1,counter+1, 'velocity')

                for t_id, t in enumerate(record.times):
                    data_sheet.write(t_id+2, counter, t)

                for v_id, v in enumerate(record.velocities):
                    data_sheet.write(v_id+2, counter+1, v)

                # Metadata sheet
                metadata_sheet.write(1, 0, 'ID')
                metadata_sheet.write(2, 0, 'Date')
                metadata_sheet.write(3, 0, 'Start')
                metadata_sheet.write(4, 0, 'Finish')
                metadata_sheet.write(5, 0, 'Length')
                metadata_sheet.write(6, 0, 'Mean velocity')
                metadata_sheet.write(7, 0, 'Comment')

                metadata_sheet.write(0, (counter+2)//2, record.unique_id)
                metadata_sheet.write(1, (counter+2)//2, record.rec_id)
                metadata_sheet.write(2, (counter+2)//2, record.date_hr)
                metadata_sheet.write(3, (counter+2)//2, record.start_time_hr)
                metadata_sheet.write(4, (counter+2)//2, record.finish_time_hr)
                metadata_sheet.write(5, (counter+2)//2, record.length_hr)
                metadata_sheet.write(6, (counter+2)//2, record.mean_vel)
                metadata_sheet.write(7, (counter+2)//2, record.comment)

                counter += 2

            # Formatting
            cell_format_center = workbook.add_format({'align': 'center'})
            cell_format_bold = workbook.add_format({'bold': True})
            cell_format_center_bold = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})

            metadata_sheet.set_column(0, 0, 15, cell_format_bold)
            metadata_sheet.set_column(1, (counter+2)//2-1, 20, cell_format_center)

            metadata_sheet.set_row(0, 20, cell_format_center_bold)

        workbook.close()


class Record(ABC):
    """ Abstract class for velocity records. """
    date_format = '%Y.%m.%d.'
    time_format = '%H:%M:%S'
    length_format = '%M:%S'

    @abstractmethod
    def __init__(self):
        pass

    # Subclass should implement these
    times = NotImplemented
    velocities = NotImplemented
    rec_id = NotImplemented
    start_time = NotImplemented
    finish_time = NotImplemented
    comment = NotImplemented
    sampling_freq = NotImplemented
    device_serial = NotImplemented

    @property
    def unique_id(self):
        """ A property that stores a unique id based on the start time
            of this record. Used for naming folders in the HDF5 file. """
        return '%08X' % hash(self.start_time)

    @property
    def mean_vel(self):
        """ A property that holds the mean of the recorded velocities. """
        return np.mean(self.velocities)

    @property
    def length(self):
        """ A property that holds the length of this recording in seconds. """
        return self.finish_time-self.start_time

    @property
    def date_hr(self):
        """ A property that holds the starting date in a human readable format
            defined by the data_format class variable. """
        return time.strftime(self.date_format, time.localtime(self.start_time))

    @property
    def start_time_hr(self):
        """ A property that holds the starting time in a human readable format
            defined by the time_format class variable. """
        return time.strftime(self.time_format, time.localtime(self.start_time))

    @property
    def finish_time_hr(self):
        """ A property that holds the finishing time in a human readable format
            defined by the time_format class variable. """
        return time.strftime(self.time_format, time.localtime(self.finish_time))

    @property
    def length_hr(self):
        """ A property that holds the length of the recording in a human readable
            format defined by the length_format class variable. """
        return time.strftime(self.length_format, time.localtime(self.length))

    def save(self, log_file):
        '''
        Saves this record into a file and returns a FileRecord that can replace it.

        :param log_file: An opened HDF5 file
        :type log_file: h5py.File
        '''

        log_file.create_group(self.unique_id)
        log_file[self.unique_id].attrs['id'] = self.rec_id
        log_file[self.unique_id].attrs['comment'] = self.comment
        log_file[self.unique_id].attrs['date_hr'] = self.date_hr
        log_file[self.unique_id].attrs['start_time'] = self.start_time
        log_file[self.unique_id].attrs['start_time_hr'] = self.start_time_hr
        log_file[self.unique_id].attrs['finish_time'] = self.finish_time
        log_file[self.unique_id].attrs['finish_time_hr'] = self.finish_time_hr
        log_file[self.unique_id].attrs['length'] = self.length
        log_file[self.unique_id].attrs['length_hr'] = self.length_hr
        log_file[self.unique_id].attrs['mean_velocity'] = self.mean_vel
        log_file[self.unique_id].attrs['sampling_freq'] = self.sampling_freq
        log_file[self.unique_id].attrs['device_serial'] = self.device_serial

        log_file[self.unique_id+'/time'] = self.times
        log_file[self.unique_id+'/velocity'] = self.velocities

        return FileRecord(log_file[self.unique_id])

class MemoryRecord(Record):
    """ A velocity record that is in memory ie. not saved yet. """

    def __init__(self, rec_id, sampling_freq, device_serial):
        super().__init__()

        # Data
        self.times = []
        self.velocities = []

        # Metadata
        self.rec_id = rec_id
        self.sampling_freq = float(sampling_freq)
        self.device_serial = device_serial
        self.start_time = None
        self.finish_time = None
        self.comment = ''

    def start(self):
        """ Called when recording to this record is started.
            Saves the current time as the start time. """
        self.start_time = time.time()

    def append(self, gtime, vel, rec):
        """ Appends this record with the given time and velocity
            if the recording state is 1. """
        if bool(rec):
            self.times.append(gtime)
            self.velocities.append(vel)

    def finish(self):
        """ Called then the recording to this record is finished.
            Saves the current time as the finish time. """
        self.finish_time = time.time()
        self.times = np.array(self.times, dtype=np.uint64)
        self.times -= self.times[0] # start time at 0
        self.velocities = np.array(self.velocities, dtype=float)

class FileRecord(Record):
    """ A velocity record that is saved in a HDF5 file. """

    def __init__(self, file_group):
        super().__init__()
        self.file_group = file_group
        self.m_rec_id = None
        self.m_comment = None

    @property
    def times(self):
        """ Returns the time data form file """
        return self.file_group['time'][...]

    @property
    def velocities(self):
        """ Returns the velocity data form file """
        return self.file_group['velocity'][...]

    @property
    def start_time(self):
        """ Returns the start time form file """
        return self.file_group.attrs['start_time']

    @property
    def finish_time(self):
        """ Returns the finish time form file """
        return self.file_group.attrs['finish_time']

    @property
    def rec_id(self):
        """ Returns the record's ID form file """
        if self.m_rec_id is None:
            return int(self.file_group.attrs['id'])
        else:
            return self.m_rec_id

    @rec_id.setter
    def rec_id(self, value):
        """ Sets the record's ID in the file """
        self.m_rec_id = value

    @property
    def comment(self):
        """ Returns the record's comment form file """
        if self.m_comment is None:
            return self.file_group.attrs['comment']
        else:
            return self.m_comment

    @comment.setter
    def comment(self, value):
        """ Sets the record's comment in the file """
        self.m_comment = value

    @property
    def mean_vel(self):
        """ Returns the record's mean velocity form file """
        return self.file_group.attrs['mean_velocity']

    @property
    def sampling_freq(self):
        """ Returns the record's mean velocity form file """
        return self.file_group.attrs['sampling_freq']


    def save(self, log_file):
        """ Saves the modified fields and returns itself. """
        if self.unique_id not in log_file:
            return super().save(log_file)
        else:
            if self.m_rec_id is not None:
                log_file[self.unique_id].attrs['id'] = self.m_rec_id
                self.m_rec_id = None

            if self.m_comment is not None:
                log_file[self.unique_id].attrs['comment'] = self.m_comment
                self.m_comment = None

            return self

class DummyRecord(Record):
    """ A record with random data insted of recorded velocity. Can be used for
        testing purposes. """

    def __init__(self):
        from random import randint
        from scipy.interpolate import interp1d
        super().__init__()
        self.rec_id = randint(1, 999)
        self.sampling_freq = 100.0
        self.device_serial = 42
        self.start_time = time.time()
        self.finish_time = time.time()+10
        self.times = np.linspace(0, 10_000, num=1001, dtype=np.uint64)
        vel_f = interp1d(np.linspace(0, 10_000, num=11),
                         np.random.rand(11)*50_000, kind='cubic', )
        self.velocities = vel_f(self.times).astype(float)
        self.comment = 'Fake data'
