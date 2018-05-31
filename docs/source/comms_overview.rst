Overview
========

The Gramophone is a Raw-HID (Human Interface Device). It can send and receive 65 bytes in an array. 


Packet structure
----------------
Each of the sent and received packets have a the following structure:

packet[0] - Dummy
    A dummy byte that should always be zero.

packet[1:3] - Target
    The 2 byte adress of the target of the packet. Can be anything. The response packet will have this as its Source

packet[3:5] - Source
    The 2 byte adress of the source of the packet. Can be anything. The response packet will have this as its Target

packet[5] - MSN
    A single byte that can be used for identification. The response packet will have the same MSN.

packet[6] - CMD
    The 1 byte ID of the command. See commands below.

packet[7] - Payload length
    A single byte that holds the length of the payload. The payload will only be evaluated to whis length.

packet[8:65] - Payload
    The payload of the packet.

Commands
--------
The possible user commands (values for packet[6]) are the following:

0x00 - Ping
    Whatever payload is sent with this command will be sent back as a response.

0x01 - OK response
    This is the command sent back after writing a parameter successfuly.

0x02 - FAILED response
    This is the command sent back after writing a parameter failed. The payload is the errorcode (see below).

0x04 - Get firmware info
    Get information about the firmware. The structure of the reply is explained below.

0x05 - Device state
    Check the state of the device. The device should be in 0x01 state for usage. The 0x00 state is for setup.

0x06 - Store
    Save persistent variables into the FLASH.

0x07 - Restore
    Load persistent variables from the FLASH.

0x08 - Get product info
    Get information about the product. The structure of the reply is explained below.

0x0B - Read parameter(s)
    Read the value of the parameters given in the payload. The list of parameters are given below. More that one parameter can be read in one command. The order of the values in the response will be the same as the order of the parameters in the payload of this command.

0x0C - Write parameter
    Write the parameter given by the first byte of the payload with the value that follows it.


Error codes
-----------
The codes received in the payload of a FAILED response packet can be the following:

0x00 - PACKET_FAIL_UNKNOWNCMD
    Unknown command.

0x01 - PACKET_FAIL_INVALIDCMDSYNTAX
    Invalid syntax.

0x04 - PACKET_FAIL_INVALIDPARAMSYNTAX
    Invaid parameter syntax.

0x05 - PACKET_FAIL_RANGEERROR
    Parameter out of range.

0x06 - PACKET_FAIL_PARAMNOTFOUND
    Parameter not found.

0x07 - PACKET_FAIL_VALIDFAIL
    Packet validation failed.

0x08 - PACKET_FAIL_ACCESSVIOLATION
    Access to the parameter was violated (writing read only parameter).


Parameters
----------
The following parameters can be read or written with the 0x0B and 0x0C commands:

0x01 - VSEN3V3 (float)
    Voltage on 3.3V rail.

0x02 - VSEN5V (float)
    Voltage on 5V rail.

0x03 - TSENMCU (float)
    Internal teperature of the MCU.

0x04 - TSENEXT (float)
    External temperature sensor on the board.

0x10 - ENCPOS (int32)
    Encoder position.

0x11 - ENCVEL (float + uint8)
    Encoder velocity. The float part is the velocity of the disk, the integer is 1 if the disk is moving or 0 if it is not.

0x12 - ENCVELWIN (uint16)
    Encoder velocity window size.

0x13 - ENCHOME (uint8)
    Encoder homing. 0 if the encoder is not trying to find the home position, 1 if it is homing and 2 if the home position was found.

0x14 - ENCHOMEPOS (int32)
    Encoder home position.

0x20 - DI-1 (uint8)
    Digital input 1.

0x21 - DI-2 (uint8)
    Digital input 2.

0x30 - DO-1 (uint8)
    Digital output 1.

0x31 - DO-2 (uint8)
    Digital output 2.

0x32 - DO-3 (uint8)
    Digital output 3.

0x33 - DO-4 (uint8)
    Digital output 4.

0x40 - AO (float)
    Analogue output.

0xFF - LED (uint8)
    On board LED state. 0 is off, 1 is on.

Firmware info structure
-----------------------
The firmware information received after sending the 0x04 command has the following structure.

payload[0] (uint8)
    Release

payload[1] (uint8)
    Subrelease

payload[2:4] (uint16)
    Build

payload[4:6] (uint16)
    Year

payload[6] (uint8)
    Month

payload[7] (uint8)
    Day

payload[8] (uint8)
    Hour

payload[9] (uint8)
    Minute

payload[10] (uint8)
    Second

Product info structure
----------------------
The product information received after sending the 0x08 command has the following structure:

payload[0:18] (char[18])
    Name

payload[18:24] (char[6]) 
    Revision

payload[24:28] (uint32) 
    Serial

payload[28:30] (uint16)  
    Product year

payload[30] (uint8)  
    Product month

payload[31] (uint8)
    Product day

