''' Contains the Level object '''

import os
import numpy as np
from PIL import Image

from GramophoneTools.LinMaze import LinMaze, Frame, Event, Rule
from GramophoneTools.LinMaze.Zone import Zone
from GramophoneTools.LinMaze.Tools import Stopwatch
from GramophoneTools.LinMaze.Tools.filehandler import select_file


class Level(object):
    ''' 
    An object that can be played for conditioning.
    You can add frames, events and rules to it to tune your conditioning. 
    
    :param name: The name this Level will be refered to by (eg. in the default filename when saving)
    :type name:  str

    :param screen_res: The resolution of the simulation window. Set it to the resolution of the monitor 
        if you are going to make the simulation full screen. eg.: (800,600)
    :type screen_res: tuple of ints

    :param zone_offset: Zone offset in pixels, ie. what is the position of the mouse on the screen from the left.
    :type zone_offset: int

    :param transition_width: How long should the transition (gradual fade) shold be between zones in pixels.
    :type transition_width: int

    :param rgb: Red, Green and Blue levels of the frames as floats between 0 and 1.
    :type rgb: tuple of floats
    '''

    def __init__(self, name, screen_res, zone_offset,
                 transition_width=100, rgb=(1, 1, 1)):
        print("\nCreating new VR level: ", name, "\n")
        self.name = name
        # self.screen_res = screen_res
        self.screen_width = screen_res[0]
        self.screen_height = screen_res[1]
        self.zone_offset = zone_offset
        self.transition_width = transition_width
        self.rgb = rgb

        self.rendered = False

        self.frames = []
        self.events = {}
        self.zones = []
        self.rules = []

    def __str__(self):
        level_string = self.name + '\nResolution: ' + str(self.screen_width)+'×'+str(self.screen_height) + \
            '\nZone offset: ' + str(self.zone_offset) +\
            '\nTransition width: ' + str(self.transition_width)+'\n'

        level_string += "\nBLOCKS\n"
        for frame, zone in zip(self.frames, self.zones):
            level_string += str(frame) + '\n' + str(zone) + '\n\n'

        level_string += "\nRULES\n"
        for rule in self.rules:
            level_string += 'If '+str(rule).lower() + \
                ' then '+str(rule.event).lower()+'\n'

        return level_string

    @property
    def dummy_frame(self):
        ''' A frame that looks like the begining of the level. '''
        dummy_frame = Frame.Frame(self.screen_width, self.screen_height)
        dummy_frame.texture = self.combined_frame.texture[:, :self.screen_width].astype(
            np.uint8)
        dummy_frame.made = True
        return dummy_frame

    @property
    def combined_frame(self):
        ''' All the frames combined left to right. '''
        if not self.rendered:
            self.render()

        return Frame.combine(self.frames)

    @property
    def image(self):
        ''' An image of the Level's combined frames. '''
        return self.combined_frame.make_img()

    def add_block(self, frame_type, *args, **kwargs):
        ''' Adds a block of the specified type and parameters to the level. '''

        frame_type = frame_type.lower()

        width = kwargs.get('length', 0) + self.transition_width
        height = self.screen_height
        wavelength = kwargs.get('wavelength', None)
        angle = kwargs.get('angle', None)
        random_seed = kwargs.get('random_seed', None)
        side_length = kwargs.get('side_length', None)
        filename = kwargs.get('filename', None)

        frame_maker = {  # Frame type switch
            'sine': lambda: Frame.SineWave(width, height, wavelength, angle),
            'square': lambda: Frame.SquareWave(width, height, wavelength, angle),
            'greynoise': lambda: Frame.GreyNoise(width, height, random_seed),
            'binarynoise': lambda: Frame.BinaryNoise(width, height, random_seed),
            'cloud': lambda: Frame.Cloud(width, height, random_seed),
            'marble': lambda: Frame.Marble(width, height, random_seed),
            'wood': lambda: Frame.Wood(width, height, random_seed),
            'checkerboard': lambda: Frame.Checkerboard(width, height, side_length),
            'image': lambda: Frame.ImageFile(height, filename)
        }.get(frame_type, None)

        if frame_maker is None:
            raise ValueError(
                'Error: \'{}\' is not a valid frame_type'.format(frame_type))
        frame = frame_maker()

        # New zone starts at the end of the last one
        if self.zones:
            begin = self.zones[-1].end
            end = self.zones[-1].end + frame.width - self.transition_width
        else:  # Fist zone starts at 0
            begin = 0
            end = frame.width - self.transition_width
        zone = Zone(begin, end, kwargs.get('zone_type', 'generic'))

        self.frames.append(frame)
        self.zones.append(zone)

        print("\nAdded block to " + self.name + ":")
        print(str(frame))
        print(str(zone))

    def add_event(self, name, event_type, *args):
        ''' 
        Adds an Event to the level which can be triggered by Rules.

        :param name: The name this Event can be referenced by
        :type name: string

        :param event_type: type of the event can be 'teleport', 'random_teleport', 
            'start_burst', 'stop_burst', 'port_on', 'port_off', 'pause', 'unpause'
        :type event_type: string

        :param args: The arguments for the Event of the given type.
        '''

        if event_type == "teleport":
            self.events[name] = Event.Teleport(self, args[0])

        if event_type == "random_teleport":
            self.events[name] = Event.RandomTeleport(self, args[0])

        if event_type == "start_burst":
            self.events[name] = Event.StartBurst(
                self, args[0], args[1], args[2])

        if event_type == "stop_burst":
            self.events[name] = Event.StopBurst(self, args[0])

        if event_type == "port_on":
            self.events[name] = Event.PortOn(self, args[0])

        if event_type == "port_off":
            self.events[name] = Event.PortOff(self, args[0])

        if event_type == "pause":
            self.events[name] = Event.Pause(self, args[0])

        if event_type == "unpause":
            self.events[name] = Event.UnPause(self, args[0])

    def add_rule(self, rule_type, event_name, *args):
        '''
        Adds a rule that triggers events based on animal behaviour.

        :param rule_type: The type of this rule, can be 'zone', 'velocity' or 'speed'.
        :type rule_type: string

        :param event_name: The name of the Event this Rule can trigger.
        :type event_name: string

        :param args: The arguments for the Rule of the given type.
        '''
        if rule_type == "zone":
            self.rules.append(Rule.ZoneRule(
                self, self.events[event_name], args[0], args[1]))

        if rule_type == "velocity":
            self.rules.append(Rule.VelocityRule(
                self, self.events[event_name], args[0], args[1], args[2]))

        if rule_type == "speed":
            self.rules.append(Rule.SpeedRule(
                self, self.events[event_name], args[0], args[1], args[2]))

    def render(self):
        ''' Renders all the frames of the level, making it ready to be played. '''
        if not self.rendered:
            print("\nRendering", self.name + ':')
            self.frames = Frame.multi_make(self.frames)
            Frame.transition(self.frames, self.transition_width)
            self.rendered = True

    def show_image(self):
        ''' Displays the level as a picture '''
        self.image.show()

    def save_image(self):
        ''' Saves the picture of the Level '''
        filename = select_file(defaultextension='.bmp',
                               filetypes=[('VR Level image', '.bmp')],
                               title='Save image of Level',
                               initialdir=os.getcwd(),
                               initialfile=self.name)
        self.image.convert('RGB').save(filename)

    def save_summary(self):
        ''' Saves a human readable summary of the Level '''
        filename = select_file(defaultextension='.txt',
                               filetypes=[('Text summary', '.txt')],
                               title='Save summary of Level',
                               initialdir=os.getcwd(),
                               initialfile=self.name)

        with open(filename, 'w') as summary_file:
            summary_file.write(str(self))

    def play(self, *args, **kwargs):
        '''
        Plays the Level by making a Session for it.

        :param args: Arguments of the Session created.
        :param kwargs: Keyword arguments of the Session created.

        '''
        LinMaze.Session(self, *args, **kwargs)
        # play_session.start()
