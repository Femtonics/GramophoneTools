''' Events define something that can happen while the level is being played. Triggered by rules. '''


class Event(object):
    ''' 
    Generic Event object all specific Events inherit from.

    :param level: The Level this Event will be used on
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


    @property
    def triggerable(self):
        ''' Tell whether it makes sense to trigger this event at the moment. '''
        return True

    def set_session(self, session):
        ''' 
        Sets the Session the event will be triggered in. 

        :param session: The session this Event will be triggered in
        :type session: Session
        '''
        self.session = session


class Teleport(Event):
    '''
    Teleports to a set location 
    
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

    :param port: Which output to use on the device.
    :type port: str -- 'A', 'B' or 'C'
    '''

    def __init__(self, level, port):
        super().__init__(level)
        self.port = port.upper()

    def trigger(self):
        self.session.gramophone.port_on(self.port)
        super().trigger()

    def __str__(self):
        return "Turn ON port " + str(self.port)

    @property
    def triggerable(self):
        return not bool(self.session.gramophone.ports[self.port].state)


class PortOff(Event):
    '''
    Turns off a port on the Level's Gramophone.

    :param port: Which output to use on the device.
    :type port: str -- 'A', 'B' or 'C'
    '''

    def __init__(self, level, port):
        super().__init__(level)
        self.port = port.upper()

    def trigger(self):
        self.session.gramophone.port_off(self.port)
        super().trigger()

    @property
    def triggerable(self):
        return bool(self.session.gramophone.ports[self.port].state)

    def __str__(self):
        return "Turn OFF port " + str(self.port)


class StartBurst(Event):
    ''' Starts bursting a port on the Level's gramophone '''

    def __init__(self, level, port, on_time, pause_time):
        super().__init__(level)
        self.port = port.upper()
        self.on_time = on_time
        self.pause_time = pause_time

    def trigger(self):
        self.session.gramophone.start_burst(
            self.port, self.on_time, self.pause_time)
        super().trigger()

    @property
    def triggerable(self):
        return not self.session.gramophone.ports[self.port].bursting

    def __str__(self):
        return "Start " + str(self.on_time) + " sec bursts with " \
            + str(self.pause_time) + " sec pauses on port " + str(self.port)


class StopBurst(Event):
    ''' Stops bursting a port on the Level's gramophone '''

    def __init__(self, level, port):
        super().__init__(level)
        self.port = port.upper()

    def trigger(self):
        self.session.gramophone.stop_burst(self.port)
        super().trigger()

            # print("Bursting is already off on port", self.port, '\n')
    @property
    def triggerable(self):
        return self.session.gramophone.ports[self.port].bursting

    def __str__(self):
        return "Stop the bursts on port " + str(self.port)


class Pause(Event):
    ''' Pauses the Level where it is or at a given position '''

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
        pos_name = 'current' if self.pause_position is None else str(self.pause_position)
        return "Pause at " + pos_name + " position"


class UnPause(Event):
    ''' Unpauses the Level where it is or at a given position '''

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
        pos_name = 'current' if self.unpause_position is None else str(self.unpause_position)
        return "Unpause at " + pos_name + " position"
