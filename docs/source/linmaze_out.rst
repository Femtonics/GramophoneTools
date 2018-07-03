Log file structure
==================

LinMaze sessions are logged into an HDF5 file with a .vrl extension. 

The file has the following structure:

time
    time axis, array of float values of the computer's time in seconds
g_time
    time axis, array of integer values of the gramophone's time in tenths of a millisecond
paused
    array of zeros and ones, value is 1 if the simulation was paused at that point
input_1
    the satte of the digital input 1, 1 is high 0 is low
input_2
    the satte of the digital input 2, 1 is high 0 is low
output_1
    the satte of the digital output 1, 1 is high 0 is low
output_2
    the satte of the digital output 2, 1 is high 0 is low
output_3
    the satte of the digital output 3, 1 is high 0 is low
output_4
    the satte of the digital output 4, 1 is high 0 is low
position
    the position in the maze in pixels
teleport
    array of zeros and ones, 1 if there was a teleport at that point
velocity
    array of signed integers with the velocity in pixels/record
zone
    n×m matrix of ones and zeros. Each column is an array of ones and zeros for that zone
zone_types
    a group of arrays of zeros and ones for each zone type that was defined

    zone_types/example
        1 when the mouse was in an 'example' zone, 0 otherwise
