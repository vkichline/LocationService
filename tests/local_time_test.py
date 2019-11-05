#!/usr/bin/env python3

import sys, random
sys.path.append('../')
import astro as a
from TimeCalc import TimeCalc

tc = TimeCalc(89, 0)
for lon in range(-180, 181):
    tc.change_location(89, lon)
    print(lon, '\t', tc.getTimeZoneName(), '\t', tc.getLocalTime())

# Check for exceptions with random locations
for x in range(1000):
    lat = random.random() * 180.0 - 90.0
    lon = random.random() * 360.0 - 180.0
    tc.change_location(lat, lon)
    t = tc.getTimeZoneName()
    print(lat, '\t', lon, '\t', t)
