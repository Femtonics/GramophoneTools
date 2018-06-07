Static functions
================
Functions that work with Frame objects.

.. automodule:: Frame
   :members: multi_make, transition, combine


Abstract Frame classes
======================
Abstract classes for all Frames to inherit from.

Frame
-----
.. autoclass:: Frame.Frame
   :members:

Random Frame
------------
.. autoclass:: Frame.RandomFrame
   :members:
   :show-inheritance:

Wave Frame
----------
.. autoclass:: Frame.WaveFrame
   :members:
   :show-inheritance:

Specific Frames
===============
All the different types of Frames you can make.

Binary noise
------------
.. autoclass:: Frame.BinaryNoise
   :members:
   :show-inheritance:

Greyscale noise
---------------
.. autoclass:: Frame.GreyNoise
   :members:
   :show-inheritance:


Checkerboard pattern
--------------------
.. autoclass:: Frame.Checkerboard
   :members:
   :show-inheritance:


Cloud pattern
-------------
.. autoclass:: Frame.Cloud
   :members:
   :show-inheritance:


Marble pattern
--------------
.. autoclass:: Frame.Marble
   :members:
   :show-inheritance:
   
Wood grain pattern
------------------
.. autoclass:: Frame.Wood
   :members:
   :show-inheritance:
   

Sine wave modulated grating
---------------------------
.. autoclass:: Frame.SineWave
   :members:
   :show-inheritance:
   

Square wave modulated grating
-----------------------------
.. autoclass:: Frame.SquareWave
   :members:
   :show-inheritance:
   

Image file as Frame
-------------------
.. autoclass:: Frame.ImageFile
   :members:
   :show-inheritance:
