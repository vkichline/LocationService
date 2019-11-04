#!/usr/bin/env python3

import sys
sys.path.append('../')
import astro as a
import DayCalc, TimeCalc, sys
from datetime import datetime, timedelta
from pytz import timezone

def usage():
    print('### Usage: %s year month day' % sys.argv[0])
    sys.exit(1)

args = len(sys.argv)
if args != 4: usage()
year  = int(sys.argv[1])
month = int(sys.argv[2])
day   = int(sys.argv[3])

pacific = timezone('America/Los_Angeles')    
t = pacific.localize(datetime(year, month, day, 12))

# Print the DayCalc report for the given date
tester = DayCalc.DayCalc(a.home_topo.latitude.degrees, a.home_topo.longitude.degrees, a.home_topo.elevation.m, t)
tester.print_report()
print()

# Print the Astro report for the given date
a_t = a.ts.utc(t)
a.print_planets(a.home_loc, False, a_t)
print()

# Print the TimeInfo for the given date
t_utc = a_t.utc_datetime()
tcalc = TimeCalc.TimeCalc(a.home_topo.latitude.degrees, a.home_topo.longitude.degrees, t_utc)
print('UTC Time:   {0}'.format(tcalc.getUtcTime()))
print('Local Time: {0}'.format(tcalc.getLocalTime()))
print('Solar Time: {0}'.format(tcalc.getSolarTime()))
print('Time Zone:  {0}'.format(tcalc.getTimeZoneName()))
print('JDate:      {0}'.format(tcalc.getJDate()))
print('GMST:       {0}'.format(tcalc.decimalHoursToHMS(tcalc.getGMST())))
print('LMST:       {0}'.format(tcalc.decimalHoursToHMS(tcalc.getLMST())))
print('Local DOY:  {0}'.format(tcalc.getDOY(tcalc.getLocalTime())))
print('EoT:        {0}'.format(tcalc.getEoT()))
print('EoT2:       {0}'.format(tcalc.getEoT2()))
