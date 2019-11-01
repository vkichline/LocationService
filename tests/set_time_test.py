#!/usr/bin/env python3

import time, signal, threading, json, datetime, os
from gps import *

MAXIMUM_TIME_DIFFERENCE = 10


def check_set_system_time(self, report):
    report['mode'] = 2 # hack
    if report['mode'] >= 2:
        self.system_time_has_been_set = True
        rep_time = datetime.datetime.strptime(report['time'], '%Y-%m-%dT%H:%M:%S.%f%z')
        sys_time = datetime.datetime.now(datetime.timezone.utc)
        time_diff = abs((sys_time - rep_time).total_seconds())
        print('Report time  = %s' % (rep_time))
        print('Current time = %s' % (sys_time))
        print('Time diff = %s' % (time_diff))
        if time_diff > MAXIMUM_TIME_DIFFERENCE:
            print('Sys time = %s' % (sys_time))
            print('GSP time = %s' % (rep_time))
            print('System time differes from GPS time by %s. Updating.' % (time_diff))
            os.system('date -s ' + report['time'])

class Dummy:
    system_time_has_been_set = False

report = {'mode': 2, 'time': '2019-10-03T00:18:00.000Z'}
check_set_system_time(Dummy(), report)


#2019-10-02T19:39:24.000Z
#2019-10-02 19:39:24+00:00
#2019-10-02 12:39:25.268564

