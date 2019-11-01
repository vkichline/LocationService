#!/usr/bin/env python

import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 9999         # The port used by the server

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall(b'gps')
data = s.recv(1024)

print('Received', data.decode('utf-8'))
