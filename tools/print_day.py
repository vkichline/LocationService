#!/usr/bin/env python3

import sys, socket, json
sys.path.append('../')
import astro as a


HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 9999         # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'gps')
    data = s.recv(1024)
str = data.decode('utf-8')
gps = json.loads(str)

t = a.now()
loc = a.loc_from_data(gps['lat'], gps['lon'], gps['alt'])

a.print_planets(loc, False, t)
