''' Everything related to making LinMaze Frames. '''
import os
import math
from time import sleep
from multiprocessing import Pool

import cv2
import dill as pickle
import numpy as np
from PIL import Image

from GramophoneTools.LinMaze import perlin
from GramophoneTools.LinMaze.Tools import Stopwatch, progressbar


def multi_make(list_of_frames):
    ''' 
    Renders a list of frames with multiprocessing.

    :param list_of_frames: A list of Frame objects that sould be rendered.
    :type list_of_frames: [Frame]

    :returns: A list of rendered Frames.
     '''

    pool = Pool()
    runtime = Stopwatch.Stopwatch()

    results = pool.imap(Frame.ext_make, list_of_frames)
    pool.close()

    while results._index < len(list_of_frames):
        progressbar.printProgressBar(results._index, len(
            list_of_frames), prefix=' Rendering', suffix='  (' + str(runtime) + ')')
        sleep(0.1)
    progressbar.printProgressBar(results._index, len(
        list_of_frames), prefix=' Rendering', suffix='  (' + str(runtime) + ')')
    pool.join()
    print()
    return list(results)


def transition(list_of_frames, transition_width):
    ''' 
    Makes a list of frames with smooth transitions between them.

    :param list_of_frames: A list of Frame objects without transitions.
    :type list_of_frames: [Frame]

    :param transition_width: The width of the smooth transition between the given Frames in pixels.
    :type transition_width: int

    :returns: A list of Frames with transitions.
    '''
    frames = list_of_frames
    if transition_width > 0:
        if transition_width % 2:
            transition_width += 1
        tw1 = transition_width
        transitions = []

        decrease = np.linspace(1, 0, tw1)
        increase = np.linspace(0, 1, tw1)
        for fid in range(len(frames))[:-1]:
            transitions.append(np.round(decrease * frames[fid].frame[:, -tw1:]) +
                               np.round(increase * frames[fid + 1].frame[:, :tw1]))

        transitions.append(np.round(decrease * frames[-1].frame[:, -tw1:]) +
                           np.round(increase * frames[0].frame[:, :tw1]))

        tw2 = transition_width // 2
        for tid in range(len(transitions))[:-1]:
            frames[tid].frame = frames[tid].frame[:, :-tw2]
            frames[tid].frame[:, -tw2:] = transitions[tid][:, :tw2]
            frames[tid + 1].frame = frames[tid + 1].frame[:, tw2:]
            frames[tid + 1].frame[:, :tw2] = transitions[tid][:, -tw2:]

        frames[-1].frame = frames[-1].frame[:, :-tw2]
        frames[-1].frame[:, -tw2:] = transitions[-1][:, :tw2]

        frames[0].frame = frames[0].frame[:, tw2:]
        frames[0].frame[:, :tw2] = transitions[-1][:, -tw2:]

    # Remake textures
    for frame in frames:
        frame.make_texture()
    return frames


def combine(list_of_frames):
    '''
    Makes a Frame that is a combination of a list of Frames.

    :param list_of_frames: A list of Frame objects without transitions.
    :type list_of_frames: [Frame]

    :returns: Frame
    '''
    combined = list_of_frames[0].texture
    for fid in range(len(list_of_frames) - 1):
        combined = np.concatenate(
            (combined, list_of_frames[fid + 1].texture), axis=1)

    combined_frame = Frame(combined.shape[1], combined.shape[0])
    combined_frame.texture = combined
    combined_frame.made = True
    return combined_frame


class Frame(object):
    '''
    The visual component of the blocks that the mouse navigates in.

    :param width: The width of the Frame in pixels.
    :type width: int

    :param height: The height of the Frame in pixels.
    :type height: int

    :param rgb: The Red, Green and Blue levels of the Frame.
    :type rgb: (float, float, float)
    '''
    frame_id = 0
    display_name = "Frame"

    def __init__(self, width, height, rgb=(1, 1, 1)):
        Frame.frame_id += 1
        self.frame_id = Frame.frame_id
        self.width = int(width)
        self.height = int(height)
        self.frame = None
        self.texture = None
        self.made = False
        self.rgb = rgb

    def __str__(self):
        string = "Frame #" + str(self.frame_id).ljust(2) + \
            " - Size: " + str(self.width) + "×" + str(self.height)
        return string

    def __eq__(self, other):
        ''' Compares Frames based on type and all properties except id. '''
        return type(self) is type(other) and \
            list(self.__dict__.items())[1:] == list(other.__dict__.items())[1:]

    def __hash__(self):
        ''' The hash of the Frame. '''
        import binascii
        hash_keys = ['width', 'height', 'seed',
                     'side_length', 'wavelength', 'angle']
        hash_comps = [self.__dict__.get(key) for key in hash_keys]
        hash_comps = [comp for comp in hash_comps if comp is not None]
        hash_string = str(type(self)) + str(hash_comps)
        frame_hash = binascii.crc32(hash_string.encode('utf-8')) & 0xFFFFFFFF
        return int(frame_hash)

    @staticmethod
    def ext_make(frame):
        '''
        Tries to load the given Frame from cache or makes it and returns
        the rendered Frame.
        '''
        frame.make()
        return frame

    def make(self):
        ''' Renders the Frame. '''
        self.make_texture()
        self.made = True

    def make_img(self):
        ''' Makes a PIL Image of the Frame. '''
        if not self.made:
            self.make()
        return Image.fromarray(np.flip(self.texture, 0))

    def show_img(self):
        ''' Displays the bitmap image of the Frame. '''
        self.make_img().show()

    def save_img(self, filename):
        '''
        Saves the bitmap image of the Frame with the given filename.

        :param filename: The filename the image should be saved as.
        :type filename: str
        '''
        self.make_img().convert('RGB').save(filename)

    def make_texture(self):
        ''' Makes the Frame's texture field that stores RGB data to be used as an OpenGL texture . '''
        # Flip Frame up and down to fit with opengl indexing
        flipped_frame = np.flip(
            self.frame, 0)
        frame_r = np.round(self.rgb[0] * flipped_frame)
        frame_g = np.round(self.rgb[1] * flipped_frame)
        frame_b = np.round(self.rgb[2] * flipped_frame)
        data = np.dstack((frame_r, frame_g, frame_b))
        self.texture = data.astype(np.uint8)

    def mirror(self):
        ''' Horizontally mirrors the Frame '''
        self.frame = np.flip(self.frame, 1)


class RandomFrame(Frame):
    '''
    Abstract class all randomly generated Frames inherit from.

    :param seed: The seed of the random number generator
    '''

    def __init__(self, width, height, seed):
        super().__init__(width, height)
        self.seed = seed


class BinaryNoise(RandomFrame):
    ''' Creates a Frame with noise, that only has black and white pixels '''
    display_name = "Binary noise"

    def __str__(self):
        return super().__str__() + " - Type: Binary noise"

    def make(self):
        if self.seed is not None:
            np.random.seed(self.seed)
        self.frame = 255 * np.random.randint(2, size=(self.height, self.width))
        super().make()


class GreyNoise(RandomFrame):
    ''' Generates a frame with grayscale noise '''
    display_name = "Grayscale noise"

    def __str__(self):
        return super().__str__() + " - Type: Greyscale noise"

    def make(self):
        self.frame = np.random.randint(256, size=(self.height, self.width))
        super().make()


class Checkerboard(Frame):
    '''
    A Frame with a checkerboard pattern.

    :param side_length: The lenght of sides of the squares that make up 
        the checkerboard pattern in pixels.
    :type side_length: int
    '''
    display_name = "Checkerboard"

    def __init__(self, width, height, side_length):
        super().__init__(width, height)
        self.side_length = side_length

    def __str__(self):
        return super().__str__() + " - Type: Checkerboard - Side length: " + str(self.side_length)

    def make(self):
        self.frame = np.zeros((self.height, self.width))
        horizontal = math.ceil(self.width / (2 * self.side_length))
        vertical = math.ceil(self.height / (2 * self.side_length))

        black = np.zeros((self.side_length, self.side_length))
        white = np.ones((self.side_length, self.side_length)) * 255

        even_rows = np.concatenate(horizontal * [white, black], 1)
        odd_rows = np.concatenate(horizontal * [black, white], 1)

        block = np.concatenate(vertical * [even_rows, odd_rows], 0)
        self.frame = block[0:self.height, 0:self.width]
        super().make()


class Cloud(RandomFrame):
    ''' A Frame with a random cloud pattern in it. '''
    display_name = "Cloud"

    def __str__(self):
        return super().__str__() + " - Type: Cloud"

    def make(self):
        self.frame = perlin.cloud(self.width, self.height, self.seed)
        super().make()


class Marble(RandomFrame):
    ''' Generates a Frame with a marble pattern. '''
    display_name = "Marble"

    def __str__(self):
        return super().__str__() + " - Type: Marble"

    def make(self):
        self.frame = perlin.marble(self.width, self.height, self.seed)
        super().make()


class Wood(RandomFrame):
    ''' Generates a Frame with a wood grain pattern. '''
    display_name = "Wood"

    def __str__(self):
        return super().__str__() + " - Type: Wood"

    def make(self):
        self.frame = perlin.wood(self.width, self.height, self.seed)
        super().make()


class WaveFrame(Frame):
    '''
    Generic grating Frame, for more specific ones to inherit form.

    :param wavelength: The wavelength of the grating in pixels,
        ie. the distance between the middles of the white portions.
    :type wavelength: int

    :param angle: The angle of the graing where 0 is vertical.
    :type angle: float
    '''
    display_name = "Generic wave"

    def __init__(self, width, height, wavelength, angle):
        super().__init__(width, height)
        self.wavelength = wavelength
        self.angle = np.deg2rad(angle)
        self.wave_temp = np.linspace(0, 2 * np.pi, wavelength)

    @staticmethod
    def wave_func(val):
        ''' Trigonometric function for a sinusoidal wave. '''
        return math.ceil(127.5 + 127.5 * -1 * math.cos(val))

    def make(self):
        self.frame = np.zeros((self.height, self.width))

        def norm(x, y):
            """ Distance from origin along a line with angle. """
            return abs(math.sin(self.angle) * y + math.cos(self.angle) * x)

        for [y, x], _ in np.ndenumerate(self.frame):

            val = norm(x, y)

            val %= self.wavelength
            if val % 1:
                below = math.floor(val)
                above = math.ceil(val)
                if above == self.wavelength:
                    above = 0
                val = (1 - (val % 1)) * \
                    self.wave_temp[below] + (val % 1) * self.wave_temp[above]
            else:
                val = self.wave_temp[int(val)]
            self.frame[y, x] = val

        super().make()


class SineWave(WaveFrame):
    ''' Sine wave modulated grating pattern Frame. '''
    display_name = "Sine wave"

    def __str__(self):
        return super().__str__() + " - Type: Sine wave - Wavelength: " + \
            str(self.wavelength) + " - Angle: " + str(self.angle)

    def make(self):
        for index, val in np.ndenumerate(self.wave_temp):
            self.wave_temp[index] = WaveFrame.wave_func(val)
        super().make()

class SquareWave(WaveFrame):
    ''' Square wave modulated grating pattern Frame. '''
    display_name = "Square wave"

    def __str__(self):
        return super().__str__() + " - Type: Square wave - Wavelength: " + \
            str(self.wavelength) + " - Angle: " + str(self.angle)

    def make(self):
        for index, val in np.ndenumerate(self.wave_temp):
            self.wave_temp[index] = int(WaveFrame.wave_func(val) > 127.5) * 255
        super().make()


class ImageFile(Frame):
    """
    A Frame made from a given image file.

    :param filename: The name of the file the Frame should be made from.
    :type filename: string
    """
    display_name = "Image file"

    def __init__(self, height, filename):
        img = cv2.imread(filename)
        if img.shape[0] != height:
            target_width = round(img.shape[1]*(height/img.shape[0]))
            img = cv2.resize(img, (target_width, height))
        img = np.flip(img, 0)
        img = np.flip(img, 2)

        img_height, img_width, _ = img.shape
        super().__init__(img_width, img_height)
        self.frame = img.astype(np.uint8)

    def make(self):
        self.make_texture()
        self.made = True

    def make_texture(self):
        self.texture = self.frame
