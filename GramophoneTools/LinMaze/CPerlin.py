import ctypes
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


if __name__ == '__main__':
    import numpy as np
    from PIL import Image
    import time
    start=time.time()
    res = (400, 400)

    img = np.zeros(res)
    for x in range(res[0]):
        for y in range(res[1]):
            # print(x,y)
            # img[x][y] = int(255*perlin2d(x, y, 1/70, 5))
            g = perlin2d(x,y, 1/150, 1) * 13
            img[x][y] = 255*(g-int(g))


    img = Image.fromarray(np.transpose(img))
    # imt = img.convert('RGB')
    # img.convert('RGB').save('wood.png')
    img.convert('RGB').show()
    print('done', str(time.time()-start))
    # img.show()