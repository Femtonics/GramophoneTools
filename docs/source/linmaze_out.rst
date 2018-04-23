Log file structure
------------------

LinMaze sessions are logged into an HDF5 file with a .vrl extension. 

The file has the following structure:

analogue input
    the state of the analogue input [0,1024]
g_time
    the time of the microcontroller
paused
    array of zeros and ones, value is 1 if the simulation was paused at that point
ports
    the satte of the 3 outputs in separate arrays, 1 if the output was high, 0 if it was low
ports/A
    the states of port A
ports/B
    the states of port B
ports/C
    the states of port C
position
    the position in the maze in pixels
teleport
    array of zeros and ones, 1 if there was a teleport at that point
time
    time axis, array float values of the computers time
velocity
    array of signed integers with the velocity in pixels/record
zone
    n×m matrix of ones and zeros. Each column is an array of ones and zeros for that zone
zone_types
    a group of arrays of zeros and ones for each zone type that was defined
zone_types/generic
    1 when the mouse was in a 'generic' zone. Only zone types that were defined in the Level will be shown here.
