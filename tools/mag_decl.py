#!/usr/bin/env python3

import socket, json, geomag

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 9999         # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'gps')
    data = s.recv(1024)

jdata = data.decode('utf-8')
obj = json.loads(jdata)
decl = geomag.declination(dlat=obj['lat'], dlon=obj['lon'],h=obj['alt'])
print(decl)
