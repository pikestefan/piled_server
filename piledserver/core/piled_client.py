# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 22:08:53 2023

@author: L
""" "localhost"

import socket
from pathlib import Path
import yaml


class PILedClient:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cfg_path = Path(__file__).parents[1] / "configs/client.cfg"

        with open(cfg_path, "r") as file:
            configs = yaml.safe_load(file)

        self.host_ip = configs["host_ip"]
        self.host_port = configs["host_port"]
        self.timeout = configs["default_timeout"]

    def sendread(self, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            sock.connect((self.host_ip, self.host_port))
            try:
                sock.sendall(message.encode("utf-8"))
                reply = sock.recv(2048).decode()
                if reply == "0":
                    print("The host replied.")
                else:
                    print("Message has been sent but not reply from host.")
            except:
                print(
                    "Write/read operation has not succeded. Check that the device"
                    " at ip {}, port: {}, is still available."
                    " The current connection will be closed.".format(
                        self.host_ip, self.host_port
                    )
                )


he = PILedClient()
