#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 18 10:22:31 2023

@author: slab2pi
"""

import socket
from time import sleep
from PyQt5.QtCore import QThread, QObject, QCoreApplication, pyqtSignal, Qt, pyqtSlot
from numpy.random import randint

class ThreadedQObject(QObject):
    
    def __init__(self, threadname = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._thread = None
        self.threadname = threadname
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
        print(f"Thread {self.threadname} now closed")
        self._thread = None

class LEDServer(ThreadedQObject):
    def __init__(self, threadname, *args, **kwargs):
        super().__init__(threadname, *args, **kwargs)
        
        self._default_colors = dict()
        
        self._mythread = None
        self.ledh_ip = self._get_own_ip()
        self._port = 12345
        
        self.ledh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ledh_socket.bind((self.ledh_ip, self._port))
        
        self.connection_dictionary = dict()
        
        self.color_dictionary = dict()
        
        self.listener = ServerListener("thread_servlist", self.ledh_socket)
        self.listener.sig_ConnectionSuccess.connect(self.add_connection)
        self.listener.sig_ServerListen.emit()
        
    def assign_color(self, ip):
        pass
    
    def _get_own_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
    
    def remove_connection(self, ip):
        connection = self.connection_dictionary[ip]
        connection.stop()
        self.connection_dictionary.pop(ip)
        
    
    def add_connection(self, connection, ipaddress):
        open_connections = len(self.connection_dictionary)
        conn = ServerConnection(f"thread_{open_connections}",
                                connection,
                                ipaddress)
        conn.sig_ConnectionClosed.connect(self.remove_connection)
        self.connection_dictionary[ipaddress] = conn
        conn.sig_startListening.emit()
        
    
class ServerListener(ThreadedQObject):
    
    sig_ServerListen = pyqtSignal()
    sig_ConnectionSuccess = pyqtSignal(socket.socket, str)
    
    def __init__(self, threadname, socket_conn=None, *args, **kwargs):
        super().__init__(threadname, *args, **kwargs)
        self.socket_conn = socket_conn
        self.listen_flag = True
        
        self.sig_ServerListen.connect(self.start_listening)
        
    def start_listening(self):
        
        print("Started listening")
        self.socket_conn.listen()
        conn, address = self.socket_conn.accept()
        ip, _ = address
        
        try:
            conn.sendall(b"1")
            
            print("Connected to", ip)
            self.sig_ConnectionSuccess.emit(conn, ip)
        except:
            print(f"Sending a message to {ip} has failed.")
        
        self.sig_ServerListen.emit()
        
class ServerConnection(ThreadedQObject):
    sig_MessageRcvd = pyqtSignal(str)
    sig_ConnectionClosed = pyqtSignal(str)
    sig_startListening = pyqtSignal()
    
    
    def __init__(self, threadname, connection=None, ip=None, *args, **kwargs):
        super().__init__(threadname, *args, **kwargs)
        self.connection = connection
        self.ip = ip
        
        self.sig_startListening.connect(self.receive_messages)
        
    def receive_messages(self):
        message = self.connection.recv(2048)
        message = message.decode().strip()
        if message == "-1":
            self.connection_shutdown()
        else:
            self.connection.sendall(b"0")
            self.sig_MessageRcvd.emit(message)
            print(message)
            self.sig_startListening.emit()
                
    def connection_shutdown(self):
        self.connection.sendall(b"-1")
        self.connection.close()
        self.sig_ConnectionClosed.emit(self.ip)
        
if __name__ == "__main__":
    app = QCoreApplication([])
    a = LEDServer("test")
    app.exec_()