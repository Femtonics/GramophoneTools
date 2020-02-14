"""Contains the Level object"""

from typing import List, Union, Dict

import os
import numpy as np

from GramophoneTools.LinMaze import LinMaze, Frame, Event, Rule
from GramophoneTools.LinMaze.Zone import Zone
from GramophoneTools.LinMaze.Tools import Stopwatch, progressbar
from GramophoneTools.LinMaze.Tools.filehandler import select_file


class _Level(object):
    """An object that can be played for conditioning.
    You can add frames, events and rules to it to tune your conditioning. 

    :param name: The name this Level will be refered to by (eg. in the default filename when saving)
    :type name:  str

    :param screen_res: The resolution of the simulation window. Set it to the resolution of the monitor 
        if you are going to make the simulation full screen. eg.: (800,600)
    :type screen_res: int, int

    :param zone_offset: Zone offset in pixels, ie. what is the position of the mouse on the screen from the left.
    :type zone_offset: int

    :param transition_width: How long should the transition (gradual fade) shold be between zones in pixels.
    :type transition_width: int

    :param rgb: Red, Green and Blue levels of the frames as floats between 0 and 1.
    :type rgb: float, float, float
    """

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
        self.offset = 0

        self.rendered = False

        self.frames: List[Frame] = []
        self.events: Dict[Event] = {}
        self.zones: List[Zone] = []
        self.rules: List[Rule] = []

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
        """A frame that looks like the begining of the level."""
        dummy_frame = Frame.Frame(self.screen_width, self.screen_height)
        dummy_frame.texture = self.combined_frame.texture[:, :self.screen_width].astype(
            np.uint8)
        dummy_frame.made = True
        return dummy_frame

    @property
    def combined_frame(self):
        """All the frames combined left to right."""
        if not self.rendered:
            self.render()

        return Frame.combine(self.frames)

    @property
    def image(self):
        """An image of the Level's combined frames."""
        return self.combined_frame.make_img()

    def add_block(self, frame_type, **kwargs):
        """Adds a block of the specified type and parameters to the level."""

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
        offset = 0
        if self.zones:
            offset = self.zones[-1].offset + self.zones[-1].length
        zone = Zone(offset, frame.width, kwargs.get('zone_type', 'generic'))

        self.frames.append(frame)
        self.zones.append(zone)

        print("\nAdded block to " + self.name + ":")
        print(str(frame))
        print(str(zone))

    def add_event(self, name, event_type, *args):
        """Adds an Event to the level which can be triggered by Rules.

        :param name: The name this Event can be referenced by
        :type name: string

        :param event_type: type of the event can be 'teleport', 'random_teleport', 
            'start_burst', 'stop_burst', 'port_on', 'port_off', 'pause', 'unpause'
        :type event_type: string

        :param args: The arguments for the Event of the given type.
        """

        if event_type == "teleport":
            self.events[name] = Event.Teleport(self, args[0])

        if event_type == "random_teleport":
            self.events[name] = Event.RandomTeleport(self, args[0])

        if event_type == "teleport_to_level":
            self.events[name] = Event.RandomTeleport(args[0], args[1])

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

        if event_type == "print":
            self.events[name] = Event.Print(self, args[0])

    def add_rule(self, rule_type, event_name, *args):
        """Adds a rule that triggers events based on animal behaviour.

        :param rule_type: The type of this rule, can be 'zone', 'velocity' or 'speed'.
        :type rule_type: string

        :param event_name: The name of the Event this Rule can trigger.
        :type event_name: string

        :param args: The arguments for the Rule of the given type.
        """
        
        if rule_type == "zone":
            self.rules.append(Rule.ZoneRule(
                self, self.events[event_name], args[0], args[1]))
            # zone_type, delay

        if rule_type == "velocity":
            self.rules.append(Rule.VelocityRule(
                self, self.events[event_name], args[0], args[1], args[2]))
            # vel_rule_type, threshold, delay

        if rule_type == "smooth_velocity":
            self.rules.append(Rule.SmoothVelocityRule(
                self, self.events[event_name], args[0], args[1], args[2], args[3]))
            # bin_size, vel_rule_type, threshold, delay

        if rule_type == "speed":
            self.rules.append(Rule.SpeedRule(
                self, self.events[event_name], args[0], args[1], args[2]))
            # speed_rule_type, threshold, bin_size

        if rule_type == "keypress":
            self.rules.append(Rule.KeyPressRule(
                self, self.events[event_name], args[0]))
            # key

        if rule_type == "input":
            self.rules.append(Rule.InputRule(
                self, self.events[event_name], args[0], args[1]))
            # input_id, trigger_type

    def reset_rules(self):
        for rule in self.rules:
            if hasattr(rule, 'delay_timer'):
                rule.delay_timer.reset()

    def render(self):
        """Renders all the frames of the level, making it ready to be played."""
        if not self.rendered:
            print('\n'+self.name,  '>>\n')
            self.frames = Frame.multi_make(self.frames)
            self.frames = Frame.frame_transitions(
                self.frames, self.transition_width)

            loadtime = Stopwatch.Stopwatch()
            for count, frame in enumerate(self.frames):
                frame.make_texture()
                progressbar.printProgressBar(count, len(self.frames),
                                             prefix=' Loading  ',
                                             suffix='  (' + str(loadtime) + ')')
            progressbar.printProgressBar(len(self.frames), len(self.frames),
                                         prefix=' Loading  ',
                                         suffix='  (' + str(loadtime) + ')')
            print('\n')

            self.rendered = True

    def show_image(self):
        """Displays the level as a picture"""
        self.image.show()

    def save_image(self):
        """Saves the picture of the Level"""
        filename = select_file(defaultextension='.bmp',
                               filetypes=[('VR Level image', '.bmp')],
                               title='Save image of Level',
                               initialdir=os.getcwd(),
                               initialfile=self.name)
        self.image.convert('RGB').save(filename)

    def save_summary(self):
        """Saves a human readable summary of the Level"""
        filename = select_file(defaultextension='.txt',
                               filetypes=[('Text summary', '.txt')],
                               title='Save summary of Level',
                               initialdir=os.getcwd(),
                               initialfile=self.name)

        with open(filename, 'w') as summary_file:
            summary_file.write(str(self))

    def play(self, *args, **kwargs):
        """Plays the Level by making a Session for it.

        :param args: Arguments of the Session created.
        :param kwargs: Keyword arguments of the Session created.
        """
        try:
            LinMaze.Session(self, *args, **kwargs)
        except LinMaze.LinMazeError as err:
            print('\nERROR:', err)
            input()

    @property
    def length(self):
        return sum(zone.length for zone in self.zones)

    def get_zone_by_name(self, zone_name: str) -> Union[Zone, None]:
        try:
            return next(zone for zone in self.zones
                        if zone.zone_type == zone_name)
        except StopIteration:
            return None
    
    # @property
    # def offset(self):
    #     return self.index * self.


class LevelCollection:
    screen_width: int
    screen_height: int
    level_list: List[_Level] = []

    # def __new__(cls):
    #     print("new")
    #     return self
    #     self.screen_width, self.screen_height = screen_res
    #     cls.create_level(name, transition_width, rgb)

    def __init__(self, name, zone_offset, screen_res, *args, **kwargs):
        self.name: str = name
        self.zone_offset: int = zone_offset
        self.screen_width, self.screen_height = screen_res

        self.active_level: Union[_Level, None] = None
        self.frames: List[Frame] = []

        self._extra_args = args
        self._extra_kwargs = kwargs

    def create_level(self, name, transition_width=100, rgb=(1, 1, 1)):
        new_level = _Level(name, (self.screen_width, self.screen_height),
                           self.zone_offset, transition_width, rgb)

        self.level_list.append(new_level)
        return new_level

    def __iter__(self):
        return iter(self.level_list)

    def __len__(self):
        return len(self.level_list)

    def index(self, obj: _Level):
        return self.level_list.index(obj)

    @property
    def rendered(self):
        return all(lvl.rendered for lvl in self.level_list)

    @property
    def dummy_frame(self):
        dummy_frame = Frame.Frame(self.screen_width, self.screen_height)
        dummy_frame.texture = self.combined_frame.texture[:, :self.screen_width].astype(
            np.uint8)
        dummy_frame.made = True
        return dummy_frame

    @property
    def combined_frame(self):
        self.render()
        return Frame.combine(self.frames)

    @property
    def image(self):
        return self.combined_frame.make_img()

    def show_image(self):
        self.image.show()

    def render(self):
        self.frames = []
        for lvl in self.level_list:
            lvl.render()
            self.frames += lvl.frames  # list append

    def reset_rules(self):
        for lvl in self.level_list:
            lvl.reset_rules()

    def get_level_by_name(self, level_name: str) -> Union[_Level, None]:
        try:
            return next(level for level in self.level_list
                        if level.name == level_name)
        except StopIteration:
            return None

    def create_default_level(self):
        if not self.level_list:
            new_level = _Level("default_level",
                               (self.screen_width, self.screen_height),
                               self.zone_offset,
                               *self._extra_args,
                               **self._extra_kwargs)
            self.level_list.append(new_level)
            self.active_level = new_level

    def add_block(self, *args, **kwargs):
        """Mimics Level.add_block for compatibility"""
        self.create_default_level()
        self.active_level.add_block(*args, **kwargs)

    def add_event(self, *args, **kwargs):
        """Mimics Level.add_event for compatibility"""
        self.create_default_level()
        self.active_level.add_event(*args, **kwargs)

    def add_rule(self, *args, **kwargs):
        """Mimics Level.add_event for compatibility"""
        self.create_default_level()
        self.active_level.add_rule(*args, **kwargs)

    def all_zones(self):
        zones = []
        for level in self.level_list:
            zones += level.zones
        return zones

    def play(self, *args, **kwargs):
        if not self.level_list:
            raise RuntimeError("Level sequence is empty")

        param_starting_level = kwargs.pop('starting_level', 'default_level')
        if isinstance(param_starting_level, str):
            starting_level = self.get_level_by_name(param_starting_level)
        else:
            starting_level = param_starting_level

        if starting_level is not None:
            self.active_level = starting_level
        else:
            self.active_level = self.level_list[0]

        try:
            LinMaze.Session(self, *args, **kwargs)
        except LinMaze.LinMazeError as err:
            print('\nERROR:', err)
            input()


# compatibility rename
class Level(LevelCollection):
    pass
