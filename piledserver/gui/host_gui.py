# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 15:44:13 2023

@author: L
"""

from PyQt5.QtWidgets import (
    QMainWindow,
    QGridLayout,
    QTextEdit,
    QApplication,
    QWidget,
)
import sys
from piledserver.core.piled_host import LEDServer
from piledserver.core.threaded_modules import logHandler
import logging


class HostWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setGeometry(100,100, 600, 400)

        self.centralwid = QWidget()
        self.setCentralWidget(self.centralwid)

        self.loggingwindow = QTextEdit()

        glayout = QGridLayout()
        glayout.addWidget(self.loggingwindow)
        self.centralwid.setLayout(glayout)

        self.loghandler = None
        self.ledserver = None

        self.logger = logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        self.init_modules()

    def closeEvent(self, event):
        self.ledserver.shutdown()
        self.logger.info("The main application is now closing.")

    def init_modules(self):
        pass
        self.loghandler = logHandler()
        self.logger.addHandler(self.loghandler)
        self.loghandler.signaller.sig_MsgRcv.connect(self.set_log_text)

        self.ledserver = LEDServer("ledserver", self.logger)

    def set_log_text(self, text):
        self.loggingwindow.append(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HostWindow()
    window.show()
    sys.exit(app.exec_())
