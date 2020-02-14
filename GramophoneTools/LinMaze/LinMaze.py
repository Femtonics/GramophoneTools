import os
import random
import ctypes
import time

import h5py
import numpy as np
import pyglet
from pyglet.gl import *

from GramophoneTools.LinMaze import Rule
from GramophoneTools.LinMaze.Tools.Stopwatch import Stopwatch
from GramophoneTools.LinMaze.Tools.filehandler import select_file
from GramophoneTools import Comms
import GramophoneTools

# from typing import List, Tuple


class LinMazeError(Exception):
    """Generic Exception for LinMaze related errors."""
    pass


class VRWindow(pyglet.window.Window):
    """A pyglet window that can display VR on a given screen.

    :param session: The session that is played in this window.
    :type session: Session

    :param screen_number: Which monitor the window should display on.
    :type screen_number: int

    :param mirrored: True if the contents of this window should be 
        mirrored horizontally. False by default.
    :type mirrored: bool

    :param fullscreen: True if the window should be fullscreen. True by default.
    :type fullscreen: bool
    """

    def __init__(self, session, screen_number,
                 mirrored=False, fullscreen=True):

        self.session = session
        self.mirrored = mirrored
        disp = pyglet.window.Display()
        screens = disp.get_screens()
        screen_number -= 1
        super().__init__(self.session.collection.screen_width,
                         self.session.collection.screen_height,
                         screen=screens[screen_number],
                         resizable=False, vsync=True,
                         fullscreen=fullscreen, visible=False)

        self.set_mouse_visible(False)
        self.set_caption('LinMaze - Monitor #' + str(screen_number + 1))

        dir = os.path.dirname(__file__)
        icon = pyglet.image.load(dir+'\\res\\icon.png')
        self.set_icon(icon)

        # OpenGL init
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.session.collection.screen_width, 0,
                self.session.collection.screen_height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            if self.session.paused:
                self.session.unpause()
            else:
                self.session.pause()

        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

        for lvl in self.session.collection:
            for rule in lvl.rules:
                # Check keypress rules
                if type(rule) is Rule.KeyPressRule:
                    rule.check(symbol)

        if modifiers & pyglet.window.key.MOD_CTRL:
            if symbol == pyglet.window.key._1:
                target = int(not self.session.last_read['DO-1'])
                self.session.gramophone.write_output(1, target)

            if symbol == pyglet.window.key._2:
                target = int(not self.session.last_read['DO-2'])
                self.session.gramophone.write_output(2, target)

            if symbol == pyglet.window.key._3:
                target = int(not self.session.last_read['DO-3'])
                self.session.gramophone.write_output(3, target)

            if symbol == pyglet.window.key._4:
                target = int(not self.session.last_read['DO-4'])
                self.session.gramophone.write_output(4, target)

            if symbol == pyglet.window.key.LEFT:
                self.session.manual_vel += 5

            if symbol == pyglet.window.key.RIGHT:
                self.session.manual_vel -= 5

    def on_close(self):
        pyglet.app.exit()

    def on_draw(self):
        self.switch_to()

        # Clean canvas
        glClear(GL_COLOR_BUFFER_BIT)

        # Dispay all vr units
        for vru in self.session.vr_units:
            sy = self.session.collection.screen_height
            sx = vru["length"]

            glLoadIdentity()
            glColor3f(1.0, 1.0, 1.0)
            glBindTexture(GL_TEXTURE_2D, vru["texture_id"])

            if self.mirrored:
                glTranslatef((-1) * vru["position"] +
                             self.session.collection.screen_width -
                             vru["length"], 0, 0)

                glBegin(GL_QUADS)

                glTexCoord2f(0, 0)
                glVertex2i(sx, 0)

                glTexCoord2f(1, 0)
                glVertex2i(0, 0)

                glTexCoord2f(1, 1)
                glVertex2i(0, sy)

                glTexCoord2f(0, 1)
                glVertex2i(sx, sy)
            else:
                glTranslatef(vru["position"], 0, 0)

                glBegin(GL_QUADS)

                glTexCoord2f(1, 0)
                glVertex2i(sx, 0)

                glTexCoord2f(0, 0)
                glVertex2i(0, 0)

                glTexCoord2f(0, 1)
                glVertex2i(0, sy)

                glTexCoord2f(1, 1)
                glVertex2i(sx, sy)

            glEnd()

        if self.session.offset_arrow:
            glLoadIdentity()
            glColor3f(1.0, 0.0, 0.0)
            glTranslatef(self.session.collection.zone_offset, 0, 0)
            glBindTexture(GL_TEXTURE_2D, 0)
            glBegin(GL_TRIANGLES)
            glVertex2i(-50, 0)
            glVertex2i(50, 0)
            glVertex2i(0, 150)
            glEnd()

        glFlush()


class VRLog(object):
    """A logger for LinMaze Sessions.

    :param session: The session that should be logged.
    :type session: Session
    """

    def __init__(self, session):
        self.session = session

        # Make headers
        self.zone_types = list(
            set([zone.zone_type for zone in session.collection.all_zones()]))

        self.vrl = h5py.File(session.filename, "w")

        self.vrl.attrs['level_name'] = session.collection.name  # I'm not sure if it'd brake anything if I changed it.
        self.vrl.attrs['start_time'] = session.start_time
        self.vrl.attrs['start_time_hr'] = session.start_time_hr
        self.vrl.attrs['runtime_limit'] = str(session.runtime_limit)
        self.vrl.attrs['screen_width'] = session.collection.screen_width
        self.vrl.attrs['screen_height'] = session.collection.screen_height
        self.vrl.attrs['zone_offset'] = session.collection.zone_offset
        self.vrl.attrs['transition_width'] = session.collection.level_list[0].transition_width
        self.vrl.attrs['RGB'] = session.collection[0].rgb
        self.vrl.attrs['left_monitor'] = str(session.left_monitor)
        self.vrl.attrs['right_monitor'] = str(session.right_monitor)
        self.vrl.attrs['device_serial'] = str(session.gramophone_serial)
        self.vrl.attrs['velocity_ratio'] = session.vel_ratio
        self.vrl.attrs['software_version'] = GramophoneTools.__version__

        self.vrl.create_dataset("time", (0,),
                                maxshape=(None,), dtype=np.float64)
        self.vrl.create_dataset("g_time", (0,),
                                maxshape=(None,), dtype=np.uint64)
        self.vrl.create_dataset("velocity", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("position", (0,),
                                maxshape=(None,), dtype=np.uint64)
        self.vrl.create_dataset("teleport", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("paused", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("input_1", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("input_2", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("output_1", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("output_2", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("output_3", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("output_4", (0,),
                                maxshape=(None,), dtype=np.int8)

        zone_count = len(session.collection.all_zones())
        self.vrl.create_dataset("zone", (0, zone_count), maxshape=(
            None, zone_count), dtype=np.int8)

        for zone_type in self.zone_types:
            self.vrl.create_dataset(
                "zone_types/" + zone_type, (0,),
                maxshape=(None,),
                dtype=np.int8)

        # Make log lists
        self.time_record = []
        self.g_time_record = []
        self.vel_record = []
        self.pos_record = []
        self.teleport_record = []
        self.pause_record = []
        self.input_record_1 = []
        self.input_record_2 = []

        self.output_record_1 = []
        self.output_record_2 = []
        self.output_record_3 = []
        self.output_record_4 = []

        self.zone_id_records = np.empty((0, zone_count), dtype=bool)
        self.zone_type_records = {zt: [] for zt in self.zone_types}

    def make_entry(self, vel, g_time, in_1, in_2, out_1, out_2, out_3, out_4):
        """Makes an entry in all the session logs.

        :param vel: The velocity that sould be logged for this entry.
        :type vel: int

        :param g_time: The internal clock value of the Gramophone.
        :type g_time: int

        :param in_1: The state of digital input 1.
        :type in_1: int

        :param in_2: The state of digital input 2.
        :type in_2: int
        """
        self.time_record.append(self.session.runtime.value())
        self.g_time_record.append(g_time)
        self.vel_record.append(-vel)
        self.pos_record.append(self.session.virtual_relative_position)

        for zone_type in self.zone_types:
            self.zone_type_records[zone_type].append(
                int(self.session.current_zone.zone_type == zone_type))

        zone_row = [int(self.session.current_zone.zone_id == zone.zone_id)
                    for zone in self.session.collection.active_level.zones]
        self.zone_id_records = np.append(
            self.zone_id_records, [zone_row], axis=0)

        self.teleport_record.append(int(self.session.teleported))
        self.session.teleported = False

        self.input_record_1.append(in_1)
        self.input_record_2.append(in_2)
        self.output_record_1.append(out_1)
        self.output_record_2.append(out_2)
        self.output_record_3.append(out_3)
        self.output_record_4.append(out_4)

        self.pause_record.append(int(self.session.paused))

        if len(self.time_record) >= 600:
            self.flush_all()

    def flush_all(self):
        """Writes all temporary data to file."""

        self.flush(self.time_record, 'time')
        self.flush(self.g_time_record, 'g_time')
        self.flush(self.vel_record, 'velocity')
        self.flush(self.pos_record, 'position')
        self.flush(self.teleport_record, 'teleport')
        self.flush(self.pause_record, 'paused')
        self.flush(self.input_record_1, 'input_1')
        self.flush(self.input_record_2, 'input_2')
        self.flush(self.output_record_1, 'output_1')
        self.flush(self.output_record_2, 'output_2')
        self.flush(self.output_record_3, 'output_3')
        self.flush(self.output_record_4, 'output_4')

        for zone_type in self.zone_types:
            self.flush(
                self.zone_type_records[zone_type], "zone_types/" + zone_type)

        self.flush(self.zone_id_records, 'zone')

    def flush(self, record, field_name):
        """Writes the record list into the given field and clears it.

        :param record: The record that should be written to file.
        :type record: list or np.ndarray

        :param field_name: The name of the field in the HDF5 file this record should 
            be written into.
        :type field_name: str
        """

        if type(record) is np.ndarray:
            new_count = record.shape[0] - self.vrl[field_name].shape[0]
            self.vrl[field_name].resize(record.shape[0], axis=0)
            self.vrl[field_name][-new_count:] = record[-new_count:]
        else:
            self.vrl[field_name].resize(
                self.vrl[field_name].shape[0] + len(record), axis=0)
            self.vrl[field_name][-len(record):] = record
            del record[:]

    def close(self):
        """Record the time and close the log."""
        end_time = time.time()
        self.vrl.attrs['end_time'] = end_time
        self.vrl.attrs['end_time_hr'] = time.strftime(
            "%Y.%m.%d - %H:%M:%S", time.localtime(end_time))
        self.vrl.close()


class Session(object):
    """A play/simulation session for a LinMaze Level.

    :param collection: The LinMaze Level that will be played in this Session.
    :type collection: LevelCollection

    :param vel_ratio: The velocity read from the Gramophone is multiplied 
        with this. 1 by default.
    :type vel_ratio: float

    :param runtime_limit: How long should the simulation run in minutes. 
        Set to None to run infinitely. None by default
    :type runtime_limit: float or None

    :param left_monitor: The number of the monitor to the right of the animal. Set to 
        None to disable this monitor. 1 by default.
    :type left_monitor: int or None

    :param right_monitor: The number of the monitor to the right of the animal. Set to 
        None to disable this monitor. None by default.
    :type right_monitor: int or None

    :param gramophone_serial: The serial of the Gramophone used for the simulation.
        Set to None to find a Gramophone automatically. None by default.
    :type gramophone_serial: int or None

    :param fullscreen: Should the simulation run in fullscreen mode? True by default.
    :type fullscreen: bool

    :param offset_arrow: Should the zone_offset of the Level be shown as a red arrow on screen? 
        False by default.
    :type offset_arrow: bool

    :param skip_save: Should the saving of a log be skipped for this Session? False by default.
    :type skip_save: bool
    """

    def __init__(self, collection, vel_ratio=1, runtime_limit=None,
                 left_monitor=1, right_monitor=None, gramophone_serial=None,
                 fullscreen=True, offset_arrow=False, skip_save=False):

        self.collection = collection
        self.vel_ratio = vel_ratio
        self.runtime_limit = runtime_limit
        self.left_monitor = left_monitor
        self.right_monitor = right_monitor
        self.gramophone_serial = gramophone_serial
        self.offset_arrow = offset_arrow
        self.skip_save = skip_save
        self.manual_vel = 0  # For controlling movement with keyboard
        self.virtual_relative_position = 1

        grams = Comms.find_devices()
        if grams:
            if self.gramophone_serial is None:
                print('\nNo Gramophone specified. Using the first one.')
                self.gramophone_serial = list(grams)[0]

            self.gramophone = grams[self.gramophone_serial]
        else:
            raise(LinMazeError('No gramophones connected.'))

        self.vr_units = []
        self.runtime = Stopwatch()
        self.position = self.collection.zone_offset - 1
        self.current_zone = self.collection.active_level.zones[0]
        self.paused = False
        self.teleported = False
        self.last_position = 0

        # Render the level if it wasn't pre rendered
        if not collection.rendered:
            collection.render()

        self.calculate_level_offsets()

        # Set session for all events
        for lvl in self.collection:
            for key in lvl.events:
                lvl.events[key].set_session(self)

        # Make the window
        if left_monitor is not None:
            left_window = VRWindow(
                self, self.left_monitor, mirrored=False, fullscreen=fullscreen)
        else:
            left_window = None

        if right_monitor is not None:
            right_window = VRWindow(
                self, self.right_monitor, mirrored=True, fullscreen=fullscreen)
        else:
            right_window = None

        def main_loop(_):
            """Commands executed at each frame refresh.

            :param _: Time since last refresh is seconds.
                Passed by the pyglet clock. UNUSED
            :type _: float
            """
            # print('FPS:', 1/dt)s

            params = {}
            try:
                for key, val in self.gramophone.read_linmaze_params().items():
                    params[self.gramophone.parameters[key].name] = val

                self.last_read = params

            except Comms.GramophoneError as err:
                print("Communication ERROR:", err)
                print("Using the previously read values.")
                params = self.last_read

            velocity = round(
                self.vel_ratio*(params['ENCPOS'] - self.last_position)/14400)
            velocity += self.manual_vel
            self.last_position = params['ENCPOS']

            if self.paused:
                self.movement(0)
            else:
                self.movement(velocity)

            self.check_zone()

            if not self.skip_save:
                self.log.make_entry(velocity, params['TIME'],
                                    params['DI-1'], params['DI-2'],
                                    params['DO-1'],  params['DO-2'],
                                    params['DO-3'],  params['DO-4'])

            self.check_rules(velocity, params['DI-1'], params['DI-2'])

            if self.runtime_limit is not None and\
                    self.runtime.value() >= self.runtime_limit * 60:
                pyglet.app.exit()

        # Make an OpenGL texture from every frame's texture
        texture_ids = []
        textures = []
        for level in self.collection:
            textures += [frame.texture for frame in level.frames]
            textures.append(level.dummy_frame.texture)
        for tex in textures:
            # from PIL import Image
            # Image.fromarray(tex).show()
            sy = tex.shape[0]
            sx = tex.shape[1]
            # print('X', tex.shape[1], 'Y', tex.shape[0], 'C', tex.shape[2])

            tid = GLuint(0)
            glGenTextures(1, ctypes.byref(tid))

            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glBindTexture(GL_TEXTURE_2D, tid)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, sx, sy,
                         0, GL_RGB, GL_UNSIGNED_BYTE, tex.ctypes.data)
            glGenerateMipmap(GL_TEXTURE_2D)
            texture_ids.append(tid)

        vr_unit_end_pos = 0
        i = 0
        for level in self.collection:
            # Make VR units
            for frame in level.frames:
                unit = {"length": frame.width,
                        "texture_id": texture_ids[i],
                        "position": vr_unit_end_pos}
                self.vr_units.append(unit)
                vr_unit_end_pos = unit['position'] + unit['length']
                i += 1

            # VR unit of dummy frame
            unit = {"length": level.dummy_frame.width,
                    "texture_id": texture_ids[i],
                    "position": vr_unit_end_pos}
            self.vr_units.append(unit)
            vr_unit_end_pos = unit['position'] + unit['length']
            i += 1
        # Calculate level length
        self.virtual_length = 0
        for vru in self.vr_units:
            self.virtual_length += vru["length"]

        # Connect Gramophone, and reset outputs to 0
        self.gramophone.write_output(1, 0)
        self.gramophone.write_output(2, 0)
        self.gramophone.write_output(3, 0)
        self.gramophone.write_output(4, 0)
        self.gramophone.write_analog(0)

        # Save start date and time
        self.start_time = time.time()
        self.start_time_hr = time.strftime(
            "%Y.%m.%d - %H:%M:%S", time.localtime(self.start_time))
        default_filename = time.strftime(
            "%Y-%m-%d %H_%M", time.localtime(self.start_time)) +\
            ' (' + self.collection.name + ')'

        # Set up VR logger
        self.filename = None
        if not self.skip_save:
            self.filename = select_file(defaultextension='.vrl',
                                        filetypes=[('VR Log', '.vrl')],
                                        title='Save log for this session',
                                        initialdir=os.getcwd(),
                                        initialfile=default_filename)
            self.folder = os.path.dirname(os.path.realpath(self.filename))
            self.log = VRLog(self)

        # Show the window
        if left_window is not None:
            left_window.set_visible()
        if right_window is not None:
            right_window.set_visible()

        # Reset runtime & display start message
        self.runtime.reset()
        print("Starting VR session \n  Level(s): " + ", ".join(l.name for l in self.collection) +
              "\n  Date & Time: " + self.start_time_hr +
              "\n  Log file: " + str(self.filename) + "\n")

        if self.runtime_limit is not None:
            finish_time = self.start_time + self.runtime_limit * 60
            print("Training is limited to", self.runtime_limit,
                  'minutes. It will automatically end at',
                  time.strftime("%H:%M", time.localtime(finish_time)), '\n')

        # Reset gramophone registers
        self.gramophone.reset_time()
        self.gramophone.reset_position()

        collection.reset_rules()
        # Reset all Rule delay timers

        # Schedule main loop
        pyglet.clock.schedule(main_loop)
        # pyglet.clock.set_fps_limit(30)
        # pyglet.clock.schedule_interval(main_loop, 0.005)

        # Main app run
        pyglet.app.run()

        # After main app is closed
        # Reset outputs to 0 and disconnect the Gramophone
        self.gramophone.stop_burst(1)
        self.gramophone.stop_burst(2)
        self.gramophone.stop_burst(3)
        self.gramophone.stop_burst(4)
        self.gramophone.write_output(1, 0)
        self.gramophone.write_output(2, 0)
        self.gramophone.write_output(3, 0)
        self.gramophone.write_output(4, 0)
        self.gramophone.write_analog(0)

        # Save all remaining data
        if not self.skip_save:
            self.log.flush_all()
            self.log.close()

    def calculate_level_offsets(self):
        offset = 0
        for i, lvl in enumerate(self.collection):
            lvl.offset = offset
            offset += lvl.length + self.collection.screen_width

    def movement(self, vel):
        """Move on the map with given velocity.

        :param vel: Distance to move in pixels.
        :type vel: int
        """
        active = self.collection.active_level

        # Base movement (used to calculate others, loops around)
        self.position = -self.position  # easier to understand in positive
        self.position += vel - active.offset  # becomes relative
        self.position %= active.length  # looping
        self.position += active.offset  # back to absolute
        self.position = -self.position  # back to negative

        # Image movement
        img_move = self.position - self.vr_units[0]["position"]
        for vru in self.vr_units:
            vru["position"] += img_move

        # Virtual movement (position of the "character")
        relative_positive_position = -self.position - active.offset
        limit = active.length - self.collection.zone_offset
        if relative_positive_position > limit:
            self.virtual_relative_position = (relative_positive_position
                                              - active.length
                                              + self.collection.zone_offset)
        else:
            self.virtual_relative_position = (relative_positive_position
                                              + self.collection.zone_offset)

    def pause(self, position=None):
        """Pauses the level at the given position.

        :param position: Where should the simulation pause on the Level in pixels.
            Set to None to pause at current position. None by default.
        :type position: int or None
        """

        if not self.paused:
            if position is not None:
                self.teleport(position)
            self.paused = True

    def unpause(self, position=None):
        """Unpauses the level at the given position.

        :param position: Where should the simulation unpause on the Level in pixels.
            Set to None to unpause at current position. None by default.
        :type position: int or None
        """
        if self.paused:
            if position is not None:
                self.teleport(position)
            # for zr in self.zone_rules:
            #     zr.delay_timer.reset()
            self.paused = False

    def teleport(self, target_pos):
        """Teleports to the given position.

        :param target_pos: Where should the teleportation land in pixels.
        :type target_pos: int
        """
        self.position = -(target_pos - self.collection.zone_offset)
        self.teleported = True

    def random_teleport(self, target_zone_types):
        """Teleports to the middle of a random zone with one of the given zone types.

        :param target_zone_types: list of possible landing zone types.
        :type target_zone_types: [str]
        """

        target_selection = self.get_target_level_and_zone(*target_zone_types)
        if target_selection:
            target_level, target_zone = random.choice(target_selection)
            self.collection.active_level = target_level
        else:
            target_zone = self.current_zone

        # this is not the middle. transition_width missed
        target_zone_middle_offset = target_zone.length // 2

        self.teleport(self.collection.active_level.offset
                      + target_zone.offset
                      + target_zone_middle_offset)

    def get_target_level_and_zone(
            self, *target_zones: str):  # -> List[Tuple[Level, Zone.Zone]]:
        ret = []  # List[Tuple[Level, Zone.Zone]] = []
        print(target_zones)
        for t in target_zones:
            try:
                level_name, zone_name = t.split('.')
            except ValueError:
                level_name = self.collection.active_level.name
                zone_name = t

            level = self.collection.get_level_by_name(level_name)
            if level is None:
                print(f"Error: level with name '{level_name}' was not found.")
                continue

            zone = level.get_zone_by_name(zone_name)
            if zone is None:
                print(f"Error: zone with name '{zone_name}' "
                      f"was not found in level {level_name}.")
                continue

            ret.append((level, zone))
        return ret

    def check_zone(self):
        """Updates the current zone."""
        self.current_zone = next(zone for zone in self.collection.active_level.zones
                                 if zone.check(self.virtual_relative_position))

    def check_rules(self, vel, in_1, in_2):
        """Checks all the rules of the Level.

        :param vel: The current velocity (for velocity based rules).
        :type vel: int

        :param in_1: The state of input 1
        :type in_1: int

        :param in_2: The state of input 2
        :type in_2: int
        """

        for rule in self.collection.active_level.rules:
            # Check zone rules
            if type(rule) is Rule.ZoneRule:
                rule.check(self.current_zone.zone_type)
            # Check speed and velocity rules
            if type(rule) in [Rule.SpeedRule, Rule.VelocityRule, Rule.SmoothVelocityRule]:
                rule.check(vel)
            # Check input rules
            if type(rule) is Rule.InputRule:
                rule.check(1, in_1)
                rule.check(2, in_2)
