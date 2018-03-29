import time
from abc import ABC, abstractmethod

import h5py
import numpy as np

class VelocityLog(object):
    """ A container object for velocity recordins. Handles
        saving records to HDF5 files. """

    def __init__(self, filename):
        self.filename = filename
        self.records = []

    def save(self):
        """ Saves all records from this log to file. """
        log_file = h5py.File(self.filename, "w")

        for record in self.records:
            record.save(log_file)

        log_file.close()

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


class MemoryRecord(Record):
    """ A velocity record that is in memory ie. not saved yet. """

    def __init__(self, rec_id):
        super().__init__()

        # Data
        self.times = []
        self.velocities = []

        # Metadata
        self.rec_id = rec_id
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
        self.times = np.array(self.times, dtype=float)
        self.velocities = np.array(self.velocities, dtype=np.int8)


class FileRecord(Record):
    """ A velocity record that is saved in a HDF5 file. """

    def __init__(self, file_group):
        super().__init__()
        self.file_group = file_group

    @property
    def times(self):
        return self.file_group['time']

    @property
    def velocities(self):
        return self.file_group['velocity']

    @property
    def start_time(self):
        return self.file_group.attrs['start_time']
    
    @property
    def finish_time(self):
        return self.file_group.attrs['finish_time']
    
    @property
    def rec_id(self):
        return self.file_group.attrs['id']
    
    @rec_id.setter
    def rec_id(self, value):
        self.file_group.attrs['id'] = value

    @property
    def comment(self):
        return self.file_group.attrs['comment']

    @comment.setter
    def comment(self, value):
        self.file_group.attrs['comment'] = value

    @property
    def mean_vel(self):
        return self.file_group.attrs['mean_velocity']


class DummyRecord(Record):
    """ A record with random data insted of recorded velocity. Can be used for
        testing purposes. """

    def __init__(self):
        from random import randint
        super().__init__(randint(1, 999))
        self.start_time = time.time()
        self.finish_time = time.time()+10
        self.times = list(range(3, 10000, 3))
        self.velocities = [randint(-50, 50) for _ in self.times]
        self.comment = 'I am a dummy record'
