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

Metadata
========
The metadata of each session is saved in the attributes of the root of the file.

level_name
    The name name of the Level this simulation used
RGB
    A three element array with the ratio of Red, Green and Blue pixel values
zone_offset
    The zone offset used for this simulation ie. the virtual position of the mice on the screen
velocity_ration
    The velocity ratio used for this simulation ie. how many pixels the screen was moved for each full rotation of the wheel
transition_width
    The width of the smooth transition between each Frame of the simulation
start_time
    The time the simulation started as a UNIX timestamp
start_time_hr
    The time the simulation started in a human readable format
start_time
    The time the simulation ended as a UNIX timestamp
start_time_hr
    The time the simulation ended in a human readable format
software_version
    What version of GramophoneTools was used to make this log
screen_width
    The set width of the screen
screen_height
    The set height of the screen
runtime_limit
    The runtime limit of the simulation in minutes (or None if it was not set)
left_monitor
    The number of the monitor on the left side of the animal (or None if it was not used)
right_monitor
    The number of the monitor on the right side of the animal (or None if it was not used)
device_serial
    The serial number of the device that was used for this simulation
