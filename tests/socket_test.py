#!/usr/bin/env python3

import socket, time

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 9999         # The port used by the server

def testmsg(msg):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(msg.encode())
        data = s.recv(1024)
    print('Sent: %s. Received: %s' % (msg, data.decode('utf-8')))

#for msg in {'gps', 'sun', 'moon', 'foobar', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'}:
#    testmsg(msg)
#    time.sleep(1)

testmsg('localtime')
testmsg('gps')
testmsg('time')
testmsg('day')
testmsg('sun')
testmsg('moon')
testmsg('mercury')
testmsg('venus')
testmsg('mars')
testmsg('jupiter')
testmsg('saturn')
testmsg('uranus')
testmsg('neptune')
testmsg('pluto')
testmsg('foobar')
