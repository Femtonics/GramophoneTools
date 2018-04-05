Gramophone IO module
====================

This is the module that handles all the communication with the Gramophone device. Two different serial communication modules are available. QGramophone inherits QSerialPort from pyqt5, while SerGramophone uses the pyserial package for communication.

QGramophone
-----------

Inherits the QSerialPort form the pyqt5 package and signals out the received values.

.. automodule:: QGramophone
   :members:


SerGramophone
-------------

Uses pyserial for communication. Does not use signals, values can be read manually or in the background on a separate thread.

.. automodule:: QGramophone
   :members: