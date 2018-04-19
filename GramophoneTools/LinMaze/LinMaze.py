import os
import random
import ctypes
import time

import h5py
import numpy as np
import pyglet
from pyglet.gl import *

from GramophoneTools.LinMaze import Rule
from GramophoneTools.IO.SerGramophone import Gramophone
from GramophoneTools.LinMaze.Tools.Stopwatch import Stopwatch
from GramophoneTools.LinMaze.Tools.filehandler import select_file



class VRWindow(pyglet.window.Window):
    ''' A pyglet window that can display VR on a given screen '''

    def __init__(self, session, screen_number,
                 mirrored=False, fullscreen=True):

        self.session = session
        self.mirrored = mirrored
        disp = pyglet.window.Display()
        screens = disp.get_screens()
        screen_number -= 1
        super().__init__(self.session.level.screen_width,
                         self.session.level.screen_height,
                         screen=screens[screen_number],
                         resizable=False, vsync=True,
                         fullscreen=fullscreen, visible=False)

        self.set_mouse_visible(False)
        self.set_caption('pyVR - Monitor #' + str(screen_number + 1))

        dir = os.path.dirname(__file__)
        icon = pyglet.image.load(dir+'\\res\\icon.png')
        self.set_icon(icon)

        # OpenGL init
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.session.level.screen_width, 0,
                self.session.level.screen_height, -1, 1)
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

        if symbol == pyglet.window.key.R:
            self.session.teleport(0)

        if symbol == pyglet.window.key.M:
            self.minimize()

        if symbol == pyglet.window.key.R:
            self.session.gramophone.reset()

    def on_close(self):
        pyglet.app.exit()

    def on_draw(self):
        self.switch_to()

        # Clean canvas
        glClear(GL_COLOR_BUFFER_BIT)

        # Dispay all vr units
        for vru in self.session.vr_units:
            sy = self.session.level.screen_height
            sx = vru["length"]

            glLoadIdentity()
            glColor3f(1.0, 1.0, 1.0)
            glBindTexture(GL_TEXTURE_2D, vru["texture_id"])

            if self.mirrored:
                glTranslatef((-1) * vru["position"] +
                             self.session.level.screen_width -
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
            glTranslatef(self.session.level.zone_offset, 0, 0)
            glBindTexture(GL_TEXTURE_2D, 0)
            glBegin(GL_TRIANGLES)
            glVertex2i(-50, 0)
            glVertex2i(50, 0)
            glVertex2i(0, 150)
            glEnd()

        glFlush()


class VRLog(object):
    def __init__(self, session):
        self.session = session

        # Make headers
        self.zone_types = list(
            set([zone.zone_type for zone in session.level.zones]))

        self.vrl = h5py.File(session.filename, "w")

        self.vrl.attrs['level_name'] = session.level.name
        self.vrl.attrs['start_time'] = session.start_time
        self.vrl.attrs['start_time_hr'] = session.start_time_hr
        self.vrl.attrs['runtime_limit'] = str(session.runtime_limit)
        self.vrl.attrs['screen_width'] = session.level.screen_width
        self.vrl.attrs['screen_height'] = session.level.screen_height
        self.vrl.attrs['zone_offset'] = session.level.zone_offset
        self.vrl.attrs['transition_width'] = session.level.transition_width
        self.vrl.attrs['RGB'] = session.level.rgb
        self.vrl.attrs['left_monitor'] = str(session.left_monitor)
        self.vrl.attrs['right_monitor'] = str(session.right_monitor)
        self.vrl.attrs['gramophone_port'] = str(session.gramophone_port)
        self.vrl.attrs['velocity_ratio'] = session.vel_ratio

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
        self.vrl.create_dataset("analog_input", (0,),
                                maxshape=(None,), dtype=np.uint16)
        self.vrl.create_dataset("ports/A", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("ports/B", (0,),
                                maxshape=(None,), dtype=np.int8)
        self.vrl.create_dataset("ports/C", (0,),
                                maxshape=(None,), dtype=np.int8)

        zone_count = len(session.level.zones)
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
        self.analog_input_record = []

        self.port_records = {'A': [], 'B': [], 'C': []}
        self.zone_id_records = np.empty((0, zone_count), dtype=bool)
        self.zone_type_records = {zt: [] for zt in self.zone_types}

    def make_entry(self, vel, g_time, g_analog):
        ''' Makes an entry in all the session logs '''
        self.time_record.append(self.session.runtime.value())
        self.g_time_record.append(g_time)
        self.vel_record.append(-vel)
        self.pos_record.append(self.session.virtual_position)

        for zone_type in self.zone_types:
            self.zone_type_records[zone_type].append(
                int(self.session.current_zone.zone_type == zone_type))

        zone_row = [int(self.session.current_zone.zone_id == zone.zone_id)
                    for zone in self.session.level.zones]
        self.zone_id_records = np.append(
            self.zone_id_records, [zone_row], axis=0)

        self.teleport_record.append(int(self.session.teleported))
        self.session.teleported = False

        self.port_records['A'].append(
            int(self.session.gramophone.ports['A'].state))
        self.port_records['B'].append(
            int(self.session.gramophone.ports['B'].state))
        self.port_records['C'].append(
            int(self.session.gramophone.ports['C'].state))
        self.analog_input_record.append(g_analog)
        self.pause_record.append(int(self.session.paused))

        if len(self.time_record) >= 600:
            self.flush_all()

    def flush_all(self):
        ''' Writes all temporary data to file '''

        self.flush(self.time_record, 'time')
        self.flush(self.g_time_record, 'g_time')
        self.flush(self.vel_record, 'velocity')
        self.flush(self.pos_record, 'position')
        self.flush(self.teleport_record, 'teleport')
        self.flush(self.pause_record, 'paused')
        self.flush(self.analog_input_record, 'analog_input')

        self.flush(self.port_records['A'], 'ports/A')
        self.flush(self.port_records['B'], 'ports/B')
        self.flush(self.port_records['C'], 'ports/C')

        for zone_type in self.zone_types:
            self.flush(
                self.zone_type_records[zone_type], "zone_types/" + zone_type)

        self.flush(self.zone_id_records, 'zone')

    def flush(self, record, fieldname):
        ''' Writes the record list into the given field and clears it '''
        if type(record) is np.ndarray:
            new_count = record.shape[0] - self.vrl[fieldname].shape[0]
            self.vrl[fieldname].resize(record.shape[0], axis=0)
            self.vrl[fieldname][-new_count:] = record[-new_count:]
        else:
            self.vrl[fieldname].resize(
                self.vrl[fieldname].shape[0] + len(record), axis=0)
            self.vrl[fieldname][-len(record):] = record
            del record[:]

    def close(self):
        ''' Record the time and close the log '''
        end_time = time.time()
        self.vrl.attrs['end_time'] = end_time
        self.vrl.attrs['end_time_hr'] = time.strftime(
            "%Y.%m.%d - %H:%M:%S", time.localtime(end_time))
        self.vrl.close()


class Session(object):
    ''' A play/simulation session for a VR Level '''

    def __init__(self, level, vel_ratio=1, runtime_limit=None,
                 left_monitor=1, right_monitor=None, gramophone_port=None,
                 fullscreen=True, offset_arrow=False, skip_save=False):

        self.level = level
        self.vel_ratio = vel_ratio
        self.runtime_limit = runtime_limit
        self.left_monitor = left_monitor
        self.right_monitor = right_monitor
        self.gramophone_port = gramophone_port
        self.offset_arrow = offset_arrow
        self.skip_save = skip_save

        self.gramophone = Gramophone()
        self.vr_units = []
        self.runtime = Stopwatch()
        self.position = level.zone_offset - 1
        self.current_zone = self.level.zones[0]
        self.paused = False
        self.teleported = False

        # Render the level if it wasn't pre rendered
        if not level.rendered:
            level.render()

        # Set session for all events
        for key in self.level.events:
            self.level.events[key].set_session(self)

        # Make the window
        if left_monitor is not None:
            left_window = VRWindow(
                self, self.left_monitor, mirrored=False, fullscreen=fullscreen)
        if right_monitor is not None:
            right_window = VRWindow(
                self, self.right_monitor, mirrored=True, fullscreen=fullscreen)

        def main_loop(dt):
            ''' Commands executed at each frame refresh '''
            # print('FPS:', 1/dt)s
            # velocity = round(-self.vel_ratio * self.gramophone.bcg_v)
            velocity = round(-self.vel_ratio * self.gramophone.get_mean_vel())
            g_time, g_analog = self.gramophone.bcg_t, self.gramophone.bcg_a
            if not self.paused:
                self.movement(velocity)

            self.check_zone()
            self.check_rules(velocity)

            if not self.skip_save:
                self.log.make_entry(velocity, g_time, g_analog)

            if self.runtime_limit is not None and\
                    self.runtime.value() >= self.runtime_limit * 60:
                pyglet.app.exit()

        # pyglet.clock.set_fps_limit(30)
        pyglet.clock.schedule(main_loop)
        # pyglet.clock.schedule_interval(main_loop, 0.005)

        # Make an OpenGL texture from every frame's texture
        texture_ids = []
        textures = [frame.texture for frame in self.level.frames]
        textures.append(self.level.dummy_frame.texture)
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

        # Make VR units
        for i, frame in enumerate(self.level.frames):
            self.vr_units.append(
                {"length": frame.width - self.level.transition_width,
                 "texture_id": texture_ids[i],
                 "position": self.level.zones[i].begin})

        # VR unit of dummy frame
        self.vr_units.append(
            {"length": self.level.dummy_frame.width,
             "texture_id": texture_ids[-1],
             "position": self.level.zones[-1].end})

        # Calculate level length
        self.virtual_length = 0
        for vru in self.vr_units:
            self.virtual_length += vru["length"]

        # Connect Gramophone
        if self.gramophone_port is None:
            self.gramophone.autoconnect()
        else:
            self.gramophone.connect(self.gramophone_port)
        # self.gramophone.logFilename = self.folder + "/ErrorLog.txt"
        self.gramophone.start_bcg()

        # Save start date and time
        self.start_time = time.time()
        self.start_time_hr = time.strftime(
            "%Y.%m.%d - %H:%M:%S", time.localtime(self.start_time))
        default_filename = time.strftime(
            "%Y-%m-%d %H_%M", time.localtime(self.start_time)) +\
            ' (' + self.level.name + ')'

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
        if left_monitor is not None:
            left_window.set_visible()
        if right_monitor is not None:
            right_window.set_visible()

        # Reset runtime & display start message
        self.runtime.reset()
        self.gramophone.reset()
        print("Starting VR session \n  Level: " + self.level.name +
              "\n  Date & Time: " + self.start_time_hr +
              "\n  Log file: " + str(self.filename) + "\n")

        if self.runtime_limit is not None:
            finish_time = self.start_time + self.runtime_limit * 60
            print("Training is limited to", self.runtime_limit,
                  'minutes. It will automatically end at',
                  time.strftime("%H:%M", time.localtime(finish_time)), '\n')

        # Main app run
        pyglet.app.run()

        # After main app is closed
        self.gramophone.disconnect()

        # Save all remaining data
        if not self.skip_save:
            self.log.flush_all()
            self.log.close()

    def movement(self, vel):
        ''' Move on the map with given velocity '''

        # Base movement (used to calculate others, loops around)
        self.position += vel
        self.position %= -self.virtual_length + self.level.screen_width

        # Image movement
        img_move = self.position - self.vr_units[0]["position"]
        for vru in self.vr_units:
            vru["position"] += img_move

        # Virtual movement (position of the "character")
        limit = self.virtual_length - self.level.screen_width \
            - self.level.zone_offset

        if -self.position > limit:
            self.virtual_position = -self.position - \
                (self.virtual_length - self.level.screen_width -
                 self.level.zone_offset)
        else:
            self.virtual_position = -self.position + self.level.zone_offset

    def pause(self, position=None):
        ''' Pauses the level at the given position or
            at the current one if pos=None '''

        if not self.paused:
            if position is not None:
                self.teleport(position)
            self.paused = True

    def unpause(self, position=None):
        ''' Continues the level at the given position
            or at the current one if pos=None '''
        if self.paused:
            if position is not None:
                self.teleport(position)
            # for zr in self.zone_rules:
            #     zr.delay_timer.reset()
            self.paused = False

    def teleport(self, target_pos):
        ''' Teleports to the given position and logs the teleportation '''
        self.position = -(target_pos - self.level.zone_offset)
        self.teleported = True

    def random_teleport(self, target_zone_types):
        ''' Teleports to the middle of a random zone
        with one of the given zone types (excluding current) '''
        zone_selection = [
            zone for zone in self.level.zones
            if zone.zone_type in target_zone_types and
            zone.zone_type != self.current_zone.zone_type]

        target_zone = random.choice(zone_selection)
        middle_of_target = (target_zone.begin + target_zone.end) // 2

        self.teleport(middle_of_target)

    def check_zone(self):
        ''' Updates the current zone '''
        self.current_zone = [zone for zone in self.level.zones
                             if zone.check(self.virtual_position)][0]

    def check_rules(self, vel):
        ''' Checks all the rules of the level '''

        for rule in self.level.rules:
            # Check zone rules
            if type(rule) is Rule.ZoneRule:
                rule.check(self.current_zone.zone_type)
            # Check speed and velocity rules
            if type(rule) in [Rule.SpeedRule, Rule.VelocityRule, Rule.SmoothVelocityRule]:
                rule.check(vel)
