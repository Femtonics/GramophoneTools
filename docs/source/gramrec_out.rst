Velocity data
=============

Each .vlg file contains as many groups as many recordings were made. Each recording has a unique identifier eg.: 12EB29805B3652C7 that is the name of the group.

The groups have two datasets:

time
    An array of 64 bit floats that contain the time in milliseconds
velocity
    An array of 64 bit floats that contain the velocity in counts/second. One full rotation of the disk is 14400 counts.


Metadata
========
The metadata of each recording is saved as an attribute of the group:

id
    The id of the record set by the user
comment
    The comment of the record set by the user
mean_velocity
    The mean of the velocity in this record
date_hr
    The date of the record in a human readable format (%Y.%m.%d.)
start_time
    The start time of the record in UNIX format
start_time_hr
    The start time of the record in a human readable format (%H:%M:%S)
finish_time
    The finish time of the record in UNIX format
finish_time_hr
    The finish time of the record in a human readable format (%H:%M:%S)
length
    The length of the record in seconds
length_hr
    The length of the record in a human readable format (%M:%S)