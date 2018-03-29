import time


class Stopwatch(object):
    def __init__(self):
        self.start_time = time.time()

    def __str__(self):
        return "%5.2f sec" % (time.time() - self.start_time)

    def value(self):
        return time.time() - self.start_time

    def reset(self):
        self.start_time = time.time()
