# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 15:07:28 2023

@author: L
"""

import logging
from PyQt5.QtCore import QThread, QObject, pyqtSignal


class ThreadedQObject(QObject):
    def __init__(self, threadname=None, logger=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thread = None
        self.threadname = threadname
        self.logger = logger

        self._init_thread()

    def _init_thread(self):
        self._thread = QThread()
        self._thread.setObjectName(self.threadname)
        self.moveToThread(self._thread)
        self._thread.start()

    def stop(self):
        self._thread.exit()
        while not self._thread.isFinished():
            pass
        self.logger.info(f"Thread {self.threadname} now closed.")
        self._thread = None

    def isFinished(self):
        if self._thread is None:
            return True
        else:
            return self._thread.isFinished()


class sigHandler(ThreadedQObject):
    sig_MsgRcv = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__("sighandler_thread")


class logHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signaller = sigHandler()

    def emit(self, logmsg):
        self.signaller.sig_MsgRcv.emit(self.format(logmsg))
