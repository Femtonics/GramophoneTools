''' Triggers an event on a given criteria '''
import numpy as np
from GramophoneTools.LinMaze.Tools.Timer import Timer
from collections import deque
from statistics import mean


class Rule(object):
    ''' Generic Rule all specific Rules intherit from '''

    def __init__(self, level, event):
        self.level = level
        self.event = event
        self.done = False

    def trigger(self):
        ''' Triggers the associated event and prints out a message about it '''
        if self.event.triggerable:
            print(self, "rule triggered")
            self.event.trigger()
            self.done = True
            # print(self.event)

    def check(self):
        ''' Used to check whether the rules's event should be triggered '''
        pass


class ZoneRule(Rule):
    ''' A Rule that triggers if the animal is in a given type of zone '''

    def __init__(self, level, event, zone_type, delay):
        super().__init__(level, event)
        self.zone_type = zone_type
        self.delay = delay
        self.delay_timer = Timer(delay)
        self.active = False

    def __str__(self):
        return "In " + str(self.zone_type) + " zone for " + str(self.delay) + " sec"

    def check(self, current_zone_type):
        # print('Checking ',self)
        # print('CZ',current_zone_type)
        if current_zone_type == self.zone_type:
            if not self.active and not self.done:
                # Zone entry >> Rule activation
                self.delay_timer.reset()
                self.active = True
            if self.active and self.delay_timer.is_running() and not self.done:
                # Waiting for timer to run out
                pass
            if self.active and not self.delay_timer.is_running() and not self.done:
                # Timer ran out, trigger event
                self.trigger()
        else:
            # print('current',current_zone_type,'not in',self.zone_type)
            self.done = False
            self.active = False


class VelocityRule(Rule):
    ''' A Rule that triggers if the velocity is above or below a certain threshold '''

    def __init__(self, level, event, vel_rule_type, threshold, delay):
        super().__init__(level, event)
        self.vel_rule_type = vel_rule_type
        self.threshold = threshold
        self.delay = delay
        self.delay_timer = Timer(delay)
        self.active = False

    def __str__(self):
        return "Velocity " + str(self.vel_rule_type) + " " + str(self.threshold) +\
            " for " + str(self.delay) + " sec"

    def check(self, vel):
        if self.vel_rule_type == "above":
            if abs(vel) > self.threshold:
                self.active = True
            if abs(vel) < self.threshold:
                self.active = False
                self.done = False
                self.delay_timer.reset()

        if self.vel_rule_type == "below":
            if abs(vel) < self.threshold:
                self.active = True
            if abs(vel) > self.threshold:
                self.active = False
                self.done = False
                self.delay_timer.reset()

        if self.active and not self.done and not self.delay_timer.is_running():
            self.trigger()
            # self.delay_timer.reset()

class SmoothVelocityRule(Rule):
    ''' A Rule that triggers if the moveing average of velocity
        is above or below a certain threshold '''

    def __init__(self, level, event, bin_size, vel_rule_type, threshold, delay):
        super().__init__(level, event)
        self.vel_rule_type = vel_rule_type
        self.bin_size = bin_size
        self.vels = deque([], maxlen=bin_size)
        self.threshold = threshold
        self.delay = delay
        self.delay_timer = Timer(delay)
        self.active = False

    def __str__(self):
        return "Smooth velocity (avg. of "+str(self.bin_size)+") " \
            + str(self.vel_rule_type) + " " + str(self.threshold) \
            + " for " + str(self.delay) + " sec"

    def check(self, vel):
        self.vels.append(vel)
        smooth_vel = mean(self.vels)

        if self.vel_rule_type == "above":
            if abs(smooth_vel) > self.threshold:
                self.active = True
            if abs(smooth_vel) < self.threshold:
                self.active = False
                self.done = False
                self.delay_timer.reset()

        if self.vel_rule_type == "below":
            if abs(smooth_vel) < self.threshold:
                self.active = True
            if abs(smooth_vel) > self.threshold:
                self.active = False
                self.done = False
                self.delay_timer.reset()

        if self.active and not self.done and not self.delay_timer.is_running():
            self.trigger()
            # self.delay_timer.reset()


class SpeedRule(Rule):
    ''' A Rule that triggers if the absolute integral of the velocity on a
     given range is above or below a given threshold '''

    def __init__(self, level, event, speed_rule_type, threshold, bin_size):
        super().__init__(level, event)
        self.speed_rule_type = speed_rule_type
        self.threshold = threshold
        self.bin_size = bin_size
        self.record = np.zeros(bin_size)

    def __str__(self):
        return "Absolute sum of the last " + str(self.bin_size) + " velocities " +\
            str(self.speed_rule_type) + " " + str(self.threshold)

    def check(self, vel):
        self.record[:-1] = self.record[1:]
        self.record[-1] = abs(vel)
        norm = sum(self.record)

        if self.speed_rule_type == "above":
            if norm > self.threshold and not self.done:
                self.trigger()
            if norm <= self.threshold and self.done:
                self.done = False

        if self.speed_rule_type == "below":
            if norm <= self.threshold and not self.done:
                self.trigger()
            if norm > self.threshold and self.done:
                self.done = False

        # print('sum: ', norm)
