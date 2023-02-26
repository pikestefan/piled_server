# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 22:08:53 2023

@author: L
""" "localhost"

import socket
from pathlib import Path
import yaml


class PILedClient(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cfg_path = Path(__file__).parents[1] / "configs/client.cfg"

        with open(cfg_path, "r") as file:
            configs = yaml.safe_load(file)

        self.host_ip = configs["host_ip"]
        self.host_port = configs["host_port"]
        timeout = configs["default_timeout"]

        self.settimeout(timeout)

        try:
            self.connect((self.host_ip, self.host_port))
        except:
            print(
                "Unable to connect to host ip: {}, with port: {}.".format(
                    self.host_ip, self.host_port
                )
            )

    def close_connection(self):
        self.sendread("-1")

    def connect(self, address):
        super().connect(address)
        try:
            self.recv(2048).decode()
        except:
            print("Could not receive the handshake message from the host.")

    def sendread(self, message):
        try:
            self.sendall(message.encode("utf-8"))
            reply = self.recv(2048).decode()
            if reply == "-1":
                self.close()
        except:
            print(
                "Write/read operation has not succeded. Check that the device"
                " at ip {}, port: {}, is still available."
                " The current connection will be closed.".format(
                    self.host_ip, self.host_port
                )
            )
            self.close()


he = PILedClient()
