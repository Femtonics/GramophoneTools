''' Triggers an event on a given criteria '''
from statistics import mean
from collections import deque
from abc import ABC, abstractmethod

import numpy as np
import pyglet

from GramophoneTools.LinMaze import Event
from GramophoneTools.LinMaze.Tools.Timer import Timer


class Rule(ABC):
    '''
    Generic Rule all specific Rules intherit from.

    :param level: The Level this Rule is active on.
    :type level: Level

    :param event: The event the rule triggers.
    :type event: Event
    '''

    def __init__(self, level, event):
        self.level = level
        self.event = event
        self.done = False

    def trigger(self):
        ''' Triggers the associated event and prints out a message about it. '''
        if self.event.triggerable:
            print(self, "rule triggered")
            self.event.trigger()
            self.done = True
            # print(self.event)

    @abstractmethod
    def check(self):
        ''' Check whether the rules's event should be triggered. '''
        pass


class ZoneRule(Rule):
    ''' 
    A Rule that triggers if the animal is in a given type of zone.

    :param level: The Level this Rule is active on.
    :type level: Level

    :param event: The event the rule triggers.
    :type event: Event

    :param zone_type: The type of Zone this Rule is active in.
    :type zone_type: str

    :param delay: How many seconds should be spent in the Zone before triggering.
    :type delay: float
    '''

    def __init__(self, level, event, zone_type, delay):
        super().__init__(level, event)
        self.zone_type = zone_type
        self.delay = delay
        self.delay_timer = Timer(delay)
        self.active = False

    def __str__(self):
        return "In " + str(self.zone_type) + " zone for " + str(self.delay) + " sec"

    def check(self, current_zone_type):
        """ 
        Check whether the Zone rule should be triggered.

        :param current_zone_type: Type of the curren zone.
        :type current_zone_type: str
        """
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
                if type(self.event) == Event.RandomTeleport:
                    self.done = False
                    self.active = False
        else:
            # print('current',current_zone_type,'not in',self.zone_type)
            self.done = False
            self.active = False


class VelocityRule(Rule):
    '''
    A Rule that triggers if the velocity is above or below a certain threshold.

    :param level: The Level this Rule is active on.
    :type level: Level

    :param event: The event the rule triggers.
    :type event: Event

    :param vel_rule_type: Type of comparison. Can be 'above' or 'below'.
    :type vel_rule_type: str

    :param threshold: Absolute velocity should be above or below this value.
    :type threshold: float

    :param delay: How long should the absolute velocity be above or below the threshold.
    :type delay: float    
    '''

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
        """ 
        Check whether the Velocity rule should be triggered.

        :param vel: The current velocity.
        :type vel: int
        """
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


class SmoothVelocityRule(VelocityRule):
    '''
    A Rule that triggers if the moveing average of velocity is above or below a certain threshold.

    :param level: The Level this Rule is active on.
    :type level: Level

    :param event: The event the rule triggers.
    :type event: Event

    :param bin_size: How many velocities should be used for calculating the moving average.
    :type bin_size: int

    :param vel_rule_type: Type of comparison. Can be 'above' or 'below'.
    :type vel_rule_type: str

    :param threshold: Smoothed absolute velocity should be above or below this value.
    :type threshold: float

    :param delay: How long should the smoothed absolute velocity be above or below the threshold.
    :type delay: float
    '''

    def __init__(self, level, event, bin_size, vel_rule_type, threshold, delay):
        super().__init__(level, event, vel_rule_type, threshold, delay)
        self.bin_size = bin_size
        self.vels = deque([], bin_size)

    def __str__(self):
        return "Smooth velocity (avg. of "+str(self.bin_size)+") " \
            + str(self.vel_rule_type) + " " + str(self.threshold) \
            + " for " + str(self.delay) + " sec"

    def check(self, vel):
        """ 
        Check whether the Smooth velocity rule should be triggered.

        :param vel: The current velocity.
        :type vel: int
        """
        self.vels.append(vel)
        smooth_vel = mean(self.vels)
        super().check(smooth_vel)


class SpeedRule(Rule):
    '''
    A Rule that triggers if the absolute integral of the velocity on a given range is above or below a given threshold.

    :param level: The Level this Rule is active on.
    :type level: Level

    :param event: The event the rule triggers.
    :type event: Event

    :param speed_rule_type: Type of comparison. Can be 'above' or 'below'.
    :type speed_rule_type: str

    :param threshold: The calculated integral should be above or below this value.
    :type threshold: float

    :param bin_size: How many velocities should be used for the integral.
    :type bin_size: int
     '''

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
        """ 
        Check whether the Speed rule should be triggered.

        :param vel: The current velocity.
        :type vel: int
        """
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



class KeyPressRule(Rule):
    """
    A Rule that triggers when a selected key on the keyboard is pressed.

    :param key: The key that triggers the rule.
    :type key: str
    """
    keys = pyglet.window.key.__dict__
    def __init__(self, level, event, key):
        super().__init__(level, event)
        self.key = key.upper()

    def __str__(self):
        return self.key + " keypress"

    def check(self, key):
        if key == self.keys[self.key]:
            self.trigger()
