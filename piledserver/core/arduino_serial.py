# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 19:48:51 2023

@author: L
"""

import serial
from piledserver.core.threaded_modules import ThreadedQObject
from PyQt5.QtCore import pyqtSignal


class LEDArduino(ThreadedQObject):
    sig_MsgWrite = pyqtSignal(str)
    sig_ArduinoReply = pyqtSignal(str)

    def __init__(self, threadname, logger, comport, *args, **kwargs):
        super().__init__(threadname, logger)

        self.sig_MsgWrite.connect(self.readwrite)

        self.serialconn = serial.Serial(comport, *args, **kwargs)

    def write(self, message):
        message += "\n"
        message = message.encode("utf-8")
        self.serialconn.write(message)

    def read(self):
        message = None
        while not message:
            message = self.serialconn.readline()

        return message.decode().strip()

    def readwrite(self, message):
        self.write(message)
        ard_reply = self.read()
        self.sig_ArduinoReply.emit(ard_reply)
