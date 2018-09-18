''' Events define something that can happen while the level is being played. Triggered by rules. '''
from abc import ABC, abstractproperty


class Event(ABC):
    ''' 
    Generic Event object all specific Events inherit from.

    :param level: The Level this Event will be used on.
    :type level: Level
    '''

    def __init__(self, level):
        self.level = level
        self.session = None
        self.trigger_count = 0

    def trigger(self):
        ''' Triggers the Event. Prints Event information. '''
        self.trigger_count += 1
        print(self, "["+str(self.trigger_count)+"]", '\n')

    @abstractproperty
    def triggerable(self):
        ''' Tell whether it makes sense to trigger this event at the moment. '''
        pass

    def set_session(self, session):
        ''' 
        Sets the Session the event will be triggered in. 

        :param session: The session this Event will be triggered in.
        :type session: Session
        '''
        self.session = session


class Teleport(Event):
    '''
    Teleports to a set location 

    :param level: The Level this Event will be used on.
    :type level: Level

    :param target_position: The target of the teleportation.
    :type target_position: int
    '''

    def __init__(self, level, target_position):
        super().__init__(level)
        self.target_position = target_position

    def trigger(self):
        self.session.teleport(self.target_position)
        super().trigger()

    @property
    def triggerable(self):
        return not self.session.paused

    def __str__(self):
        return "Teleport to position " + str(self.target_position)


class RandomTeleport(Event):
    ''' 
    Teleports to a type of zone that is on the given list randomly. 

    :param level: The Level this Event will be used on.
    :type level: Level

    :param list_of_target_zones: The possible Zones this teleport can land is.
    :type list_of_target_zones: [Zone]
    '''

    def __init__(self, level, list_of_target_zones):
        super().__init__(level)
        self.list_of_target_zones = list_of_target_zones

    def trigger(self):
        self.session.random_teleport(self.list_of_target_zones)
        super().trigger()

    @property
    def triggerable(self):
        return not self.session.paused

    def __str__(self):
        return "Teleport to a random zone with type: " + str(self.list_of_target_zones)


class PortOn(Event):
    '''
    Turns on a port on the Level's Gramophone.

    :param level: The Level this Event will be used on.
    :type level: Level

    :param port: Which output to use on the device.
    :type port: int
    '''

    def __init__(self, level, port):
        super().__init__(level)
        self.port = port

    def trigger(self):
        self.session.gramophone.write_output(self.port, 1)
        self.session.gramophone.read_outputs()
        super().trigger()

    def __str__(self):
        return "Turn ON port " + str(self.port)

    @property
    def triggerable(self):
        if self.port == 1:
            return not bool(self.session.gramophone.last_out_1)
        if self.port == 2:
            return not bool(self.session.gramophone.last_out_2)
        if self.port == 3:
            return not bool(self.session.gramophone.last_out_3)
        if self.port == 4:
            return not bool(self.session.gramophone.last_out_4)


class PortOff(Event):
    '''
    Turns off a port on the Level's Gramophone.

    :param level: The Level this Event will be used on.
    :type level: Level

    :param port: Which output should be turned off.
    :type port: str -- 'A', 'B' or 'C'
    '''

    def __init__(self, level, port):
        super().__init__(level)
        self.port = port

    def trigger(self):
        self.session.gramophone.write_output(self.port, 0)
        self.session.gramophone.read_outputs()
        super().trigger()

    @property
    def triggerable(self):
        if self.port == 1:
            return bool(self.session.gramophone.last_out_1)
        if self.port == 2:
            return bool(self.session.gramophone.last_out_2)
        if self.port == 3:
            return bool(self.session.gramophone.last_out_3)
        if self.port == 4:
            return bool(self.session.gramophone.last_out_4)

    def __str__(self):
        return "Turn OFF port " + str(self.port)


class StartBurst(Event):
    '''
    Starts bursting a port on the Level's gramophone.


    :param level: The Level this Event will be used on.
    :type level: Level

    :param port: Which output to use on the device.
    :type port: int

    :param on_time: How long should the port by set to high before a pause.
    :type on_time: float

    :param pause_time: How long should the pauses be.
    :type pause_time: float
    '''

    def __init__(self, level, port, on_time, pause_time):
        super().__init__(level)
        self.port = port
        self.on_time = on_time
        self.pause_time = pause_time

    def trigger(self):
        self.session.gramophone.start_burst(
            self.port, self.on_time, self.pause_time)
        super().trigger()

    @property
    def triggerable(self):
        return not self.session.gramophone.bursting[self.port]

    def __str__(self):
        return "Start " + str(self.on_time) + " sec bursts with " \
            + str(self.pause_time) + " sec pauses on port " + str(self.port)


class StopBurst(Event):
    '''
    Stops bursting a port on the Level's gramophone.

    :param level: The Level this Event will be used on.
    :type level: Level

    :param port: Which output should stop bursting.
    :type port: int
    '''

    def __init__(self, level, port):
        super().__init__(level)
        self.port = port

    def trigger(self):
        self.session.gramophone.stop_burst(self.port)
        super().trigger()

        # print("Bursting is already off on port", self.port, '\n')
    @property
    def triggerable(self):
        return self.session.gramophone.bursting[self.port]

    def __str__(self):
        return "Stop the bursts on port " + str(self.port)


class Pause(Event):
    '''
    Pauses the Level where it is or at a given position.

    :param level: The Level this Event will be used on.
    :type level: Level

    :param pause_position: Set to None to pause at current position. None by default.
    :type pause_position: int or None
    '''

    def __init__(self, level, pause_position=None):
        super().__init__(level)
        self.pause_position = pause_position

    def trigger(self):
        self.session.pause(self.pause_position)
        super().trigger()

    @property
    def triggerable(self):
        return not self.session.paused

    def __str__(self):
        pos_name = 'current' if self.pause_position is None else str(
            self.pause_position)
        return "Pause at " + pos_name + " position"


class UnPause(Event):
    '''
    Unpauses the Level where it is or at a given position.

    :param level: The Level this Event will be used on.
    :type level: Level

    :param unpause_position: Set to None to pause at current position. None by default.
    :type unpause_position: int or None
    '''

    def __init__(self, level, unpause_position=None):
        super().__init__(level)
        self.unpause_position = unpause_position

    def trigger(self):
        self.session.unpause(self.unpause_position)
        super().trigger()

    @property
    def triggerable(self):
        return self.session.paused

    def __str__(self):
        pos_name = 'current' if self.unpause_position is None else str(
            self.unpause_position)
        return "Unpause at " + pos_name + " position"


class Print(Event):
    """
    Prints the given message to the console window.

    :param message: The message that will be printed when triggered
    :type message: str
    """

    def __init__(self, level, message):
        super().__init__(level)
        self.message = message

    def __str__(self):
        return self.message

    @property
    def triggerable(self):
        return True
