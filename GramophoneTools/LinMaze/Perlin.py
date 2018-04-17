"""
Texture generation using Perlin noise
https://github.com/nikagra/python-noise
"""

import random
import math
import numpy as np

class NoiseUtils:
    
    def __init__(self, imageSize,ntype='cloud'):
        self.imageSize = imageSize
        self.gradientNumber = 256

        self.grid = [[]]
        self.gradients = []
        self.permutations = []
        self.img = {}

        self.__generateGradientVectors()
        self.__generatePermutationsTable()
        
        if ntype == 'cloud': self.makeTexture(self.cloud)
        if ntype == 'marble': self.makeTexture(self.marble)
        if ntype == 'wood': self.makeTexture(self.wood)
    
    @staticmethod
    def random_gradient_vectors(n):
        for i in range(n):
            random_angle = random.uniform(0, 2*math.pi)
            yield math.cos(random_angle), math.sin(random_angle)
    
    def __generateGradientVectors(self):
        for i in NoiseUtils.random_gradient_vectors(self.gradientNumber):
            self.gradients.append(i)
            
    def __generatePermutationsTable(self):
        self.permutations = list(range(self.gradientNumber))
        random.shuffle(self.permutations)  

    def getGradientIndex(self, x, y):
        return self.permutations[(x + self.permutations[y % self.gradientNumber]) % self.gradientNumber]

    def perlinNoise(self, x, y):
        qx0 = int(math.floor(x))
        qx1 = qx0 + 1

        qy0 = int(math.floor(y))
        qy1 = qy0 + 1

        q00 = self.getGradientIndex(qx0, qy0)
        q01 = self.getGradientIndex(qx1, qy0)
        q10 = self.getGradientIndex(qx0, qy1)
        q11 = self.getGradientIndex(qx1, qy1)

        tx0 = x - math.floor(x)
        tx1 = tx0 - 1

        ty0 = y - math.floor(y)
        ty1 = ty0 - 1
        
        v00 = self.gradients[q00][0] * tx0 + self.gradients[q00][1] * ty0
        v01 = self.gradients[q01][0] * tx1 + self.gradients[q01][1] * ty0
        v10 = self.gradients[q10][0] * tx0 + self.gradients[q10][1] * ty1
        v11 = self.gradients[q11][0] * tx1 + self.gradients[q11][1] * ty1

        wx = tx0 * tx0 * (3 - 2 * tx0)
        v0 = v00 + wx * (v01 - v00)
        v1 = v10 + wx * (v11 - v10)

        wy = ty0 * ty0 * (3 - 2 * ty0)
        return (v0 + wy * (v1 - v0)) * 0.5 + 1

    def makeTexture(self, texture):
        noise = {}
        max = min = None
        for i in range(self.imageSize[0]):
            for j in range(self.imageSize[1]):
                value = texture(i, j)
                noise[i, j] = value
                
                if max is None or max < value:
                    max = value

                if min is None or min > value:
                    min = value

        for i in range(self.imageSize[0]):
            for j in range(self.imageSize[1]):
                self.img[i, j] = (int) ((noise[i, j] - min) / (max - min) * 255 )

    def fractalBrownianMotion(self, x, y, func):
        octaves = 6 # originally 12. makes cloud more fluffy but takes longer
        amplitude = 1.0
        frequency = 1.0 / self.imageSize[0]#((self.imageSize[0]+self.imageSize[1])//2)
        persistence = 0.5
        value = 0.0
        for k in range(octaves):
            value += func(x * frequency, y * frequency) * amplitude
            frequency *= 2
            amplitude *= persistence
        return value

    def cloud(self, x, y, func = None):
        if func is None:
            func = self.perlinNoise

        return self.fractalBrownianMotion(8 * x, 8 * y, func)

    def wood(self, x, y, noise = None):
        if noise is None:
            noise = self.perlinNoise

        frequency = 1.0 / ((self.imageSize[0]+self.imageSize[1])//2)
        n = noise(4 * x * frequency, 4 * y * frequency) * 10
        return n - int(n)

    def marble(self, x, y, noise = None):
        if noise is None:
            noise = self.perlinNoise

        frequency = 1.0 / ((self.imageSize[0]+self.imageSize[1])//2)
        n = self.fractalBrownianMotion(8 * x, 8 * y, self.perlinNoise)
        return (math.sin(16 * x * frequency + 4 * (n - 0.5)) + 1) * 0.5


def makeFrame(imageSize,ntype,seed):
    if seed is not None: random.seed(seed)
    imageSize = imageSize[::-1]#reverse
    noise = NoiseUtils(imageSize,ntype)
    pixels = np.zeros(imageSize)
    for i in range(0, imageSize[0]):
        for j in range(0, imageSize[1]):
            pixels[i,j] = noise.img[i,j]
    return pixels