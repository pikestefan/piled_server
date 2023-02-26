#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 18 10:22:31 2023

@author: slab2pi
"""

import socket
import yaml
from pathlib import Path
from copy import deepcopy
from piledserver.core.threaded_modules import ThreadedQObject
from piledserver.core.arduino_serial import LEDArduino
from PyQt5.QtCore import pyqtSignal, Qt


class LEDServer(ThreadedQObject):
    def __init__(self, threadname, logger=None, *args, **kwargs):
        super().__init__(threadname, logger, *args, **kwargs)

        self.logger = logger

        self._cfg_dir = Path(__file__).parents[1] / "configs" / "host.cfg"
        with open(self._cfg_dir, "r") as file:
            self._cfgfile_cts = yaml.safe_load(file)

        self._colorcycle = [
            color
            for color in self._cfgfile_cts["default_color_cycle"]
            if color not in self._cfgfile_cts["assigned_colors"].values()
        ]

        self.baudrate = self._cfgfile_cts["arduino"]["baudrate"]
        self.comport = self._cfgfile_cts["arduino"]["comport"]

        self.arduino = LEDArduino(
            "thread_arduino", self.logger, self.comport, baudrate=self.baudrate
        )
        self.arduino.sig_ArduinoReply.connect(self.arduino_color_received)

        self.ledh_ip = self._get_own_ip()
        self._port = 12345

        ledh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ledh_socket.bind((self.ledh_ip, self._port))

        self.connection_dictionary = dict()
        self.connection_colors = dict()

        self.listener = ServerListener(
            "thread_servlist", ledh_socket, self.logger
        )
        self.listener.sig_ConnectionSuccess.connect(self.add_connection)
        self.listener.sig_StoppedListening.connect(
            self.stop_listener, Qt.QueuedConnection
        )
        self.listener.sig_ServerListen.emit()

    def assign_color(self, ip):
        if ip in self._cfgfile_cts["assigned_colors"]:
            color = self._cfgfile_cts["assigned_colors"][ip]
            self.connection_colors[ip] = color
        else:
            color = self._colorcycle.pop(0)
            self.connection_colors[ip] = color
            self._cfgfile_cts["assigned_colors"][ip] = deepcopy(color)

            with open(self._cfg_dir, "w") as file:
                yaml.dump(self._cfgfile_cts, file)

    def _get_own_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            IP = s.getsockname()[0]
        except:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP

    def remove_connection(self, ip):
        if ip in self.connection_dictionary:
            self.connection_dictionary[ip].stop()
            self.connection_dictionary.pop(ip)
            self.logger.info(f"Connection with {ip} is now closed.")
        else:
            self.logger.error(
                "Something went wrong. The IP {} is not stored in the "
                "dictionary of open connections."
            )

    def add_connection(self, connection, ipaddress):
        if ipaddress in self.connection_dictionary:
            self.logger.warning(
                f"IP {ipaddress} is already connected with the host."
                "Please close that connection first."
            )
        else:
            open_connections = len(self.connection_dictionary)
            conn = ServerConnection(
                f"thread_{open_connections}",
                connection,
                ipaddress,
                self.logger,
            )

            conn.sig_ConnectionClosed.connect(self.remove_connection)
            conn.sig_MessageRcvd.connect(self.send_color)
            self.connection_dictionary[ipaddress] = conn

            self.assign_color(ipaddress)

            self.logger.info(f"Connected to IP: {ipaddress}")
            conn.sig_startListening.emit()

    def send_color(self, message, ip):
        on_state, position = list(map(int, message.split(",")))

        color = self.connection_colors[ip]
        color = [cl * on_state for cl in color]

        message = color + [position]
        message = "{},{},{},{}".format(*message)

        self.logger.info(f"Sending {message}")

        self.arduino.sig_MsgWrite.emit(message)

    def arduino_color_received(self, message):
        self.logger.info("The arduino received the message.")

    def shutdown(self):
        self.logger.info("Shutting down the arduino...")
        self.arduino.serialconn.close()
        self.arduino.stop()
        self.logger.info("The arduino has shut down.")

        self.logger.info("Shutting down all the server connections...")
        for connection in self.connection_dictionary.values():
            connection.sig_ConnectionClosed.disconnect()
            connection.connection_shutdown()
            connection.stop()

        self.connection_dictionary = dict()
        self.logger.info("All the servers connections are now shut down.")

        self.listener.socket_conn.close()

        self.logger.info("Shutting down the LED server...")
        self.stop()
        self.logger.info("The LED server is now shut down.")

    def stop_listener(self):
        self.logger.info("Shutting down the connection listener...")
        self.listener.stop()
        self.logger.info("The listener has now been shut down.")


class ServerListener(ThreadedQObject):
    sig_ServerListen = pyqtSignal()
    sig_ConnectionSuccess = pyqtSignal(socket.socket, str)
    sig_StoppedListening = pyqtSignal()

    def __init__(
        self, threadname, socket_conn=None, logger=None, *args, **kwargs
    ):
        super().__init__(threadname, logger, *args, **kwargs)
        self.socket_conn = socket_conn
        self.listen_flag = True
        self.sig_ServerListen.connect(self.start_listening)

    def start_listening(self):
        self.logger.info("Started listening for new connections requests.")
        self.socket_conn.listen()
        try:
            conn, address = self.socket_conn.accept()
            ip, _ = address

            try:
                conn.sendall(b"1")
                self.sig_ConnectionSuccess.emit(conn, ip)
            except:
                self.logger.error(f"Sending a message to {ip} has failed.")

            self.sig_ServerListen.emit()
        except:
            self.sig_StoppedListening.emit()


class ServerConnection(ThreadedQObject):
    sig_MessageRcvd = pyqtSignal(str, str)
    sig_ConnectionClosed = pyqtSignal(str)
    sig_startListening = pyqtSignal()

    def __init__(
        self,
        threadname,
        connection=None,
        ip=None,
        logger=None,
        *args,
        **kwargs,
    ):
        super().__init__(threadname, logger, *args, **kwargs)
        self.connection = connection
        self.ip = ip

        self.logger = logger

        self.sig_startListening.connect(self.receive_messages)

    def receive_messages(self):
        try:
            message = self.connection.recv(2048)
            message = message.decode().strip()
            if message == "-1":
                self.connection_shutdown()
            else:
                try:
                    self.connection.sendall(b"0")
                    self.sig_MessageRcvd.emit(message, self.ip)
                    self.sig_startListening.emit()
                except:
                    self.logger.error(
                        "Could not send the reply message to the client, or the "
                        "client aborted the connection. "
                        "Its connection will now be closed."
                    )
                    self.connection_shutdown()
        except:
            self.logger.warning("The client aborted the connection.")
            self.sig_ConnectionClosed.emit(self.ip)

    def connection_shutdown(self):
        self.logger.info(f"Closing the communication with IP: {self.ip}.")
        try:
            self.connection.sendall(b"-1")
        except:
            self.logger.warning(
                "Could not send the connection shutdown message. Closing anyway."
            )
        self.connection.close()
        self.sig_ConnectionClosed.emit(self.ip)
