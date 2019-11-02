#!/usr/bin/env python3

import sys
sys.path.append('../')
import astro as a
import DayCalc
from datetime import datetime, timedelta
from pytz import timezone

year    = 2019
month   = 1
day     = 1
pacific = timezone('America/Los_Angeles')

    
t = pacific.localize(datetime(year, month, day))
tester = DayCalc.DayCalc(a.home_topo.latitude.degrees, a.home_topo.longitude.degrees, a.home_topo.elevation.m, t)

tester.print_report_header(False)
for day in range(365):
    tester.print_report_row(False)
    t = t + timedelta(days=1)
    tester.change_date(t)
