#!/usr/bin/env python3

import sys
sys.path.append('../')
import astro as a
from datetime import datetime, timedelta
from pytz import timezone

year    = 2019
month   = 1
day     = 1
pacific = timezone('America/Los_Angeles')


t = pacific.localize(datetime(year, month, day, 12, 0, 0))

for day in range(365):
    a.print_planets(a.home_loc, False, a.ts.utc(t))
    print()
    t = t + timedelta(days=1)
