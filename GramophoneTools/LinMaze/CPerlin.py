import ctypes
import math
import os

DIR = os.path.dirname(__file__)
perlin_lib = ctypes.CDLL(DIR+'/perlin.dll')


def perlin2d(x, y, freq, depth):
    """ Python wrapper for the c function in perlin.dll """
    c_X = ctypes.c_float(x)
    c_Y = ctypes.c_float(y)
    c_freq = ctypes.c_float(freq)
    c_depth = ctypes.c_int(depth)
    perlin_lib.perlin2d.restype = ctypes.c_float
    return perlin_lib.perlin2d(c_X, c_Y, c_freq, c_depth)


def cloud(width, height):
    img = np.zeros((width, height))
    for index, _ in np.ndenumerate(img):
        x, y = index[0], index[1]
        img[x][y] = int(255*perlin2d(x, y, 1/70, 5))
    return np.transpose(img)


def marble(width, height):
    img = np.zeros((width, height))
    for index, _ in np.ndenumerate(img):
        x, y = index[0], index[1]
        img[x][y] = perlin2d(x, y, 1/70, 5)
        img[x][y] = int(255*(math.sin(16 * x * 1/width + 4 * (img[x][y] - 0.5)) + 1) * 0.5)

    return np.transpose(img)


def wood(width, height):
    img = np.zeros((width, height))
    for index, _ in np.ndenumerate(img):
        x, y = index[0], index[1]
        g = perlin2d(x, y, 1/150, 1) * 13
        img[x][y] = 255*(g-int(g))
    return np.transpose(img)


if __name__ == '__main__':
    import numpy as np
    from PIL import Image
    import time
    start = time.time()

    cloud_img = Image.fromarray(cloud(800, 600))
    marble_img = Image.fromarray(marble(800, 600))
    wood_img = Image.fromarray(wood(800, 600))

    print('done', str(time.time()-start))

    cloud_img.convert('RGB').show()
    marble_img.convert('RGB').show()
    wood_img.convert('RGB').show()

    # cloud_img.convert('RGB').save('cloud.png')
    # wood.convert('RGB').save('wood.png')
