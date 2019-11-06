#!/usr/bin/env python3
import astro as a
from timezonefinder import TimezoneFinder
from datetime import datetime, time, timedelta
from math import pi, cos, sin, radians
import pytz

# Given the UTC time, latitude and longitude, create a TimeCalc object
# that determines the timezone, local time, sun time, sidereal time, etc.
# ctor:
# Provide uts as iso string, or datetime object
# Lat and lon can be doubles or floats, or strings representing floats.
#
# Raw Astro data: {"lon": -122.180122359, "mode": 3, "time": "2019-10-20T22:02:53.000Z", "lat": 47.725316405, "alt": 102.793, "speed": 0.628, "climb": 0.596}

class TimeCalc:
    # If utc parameter is not overridden, the current time is used.
    def __init__(self, lat, lon, utc=None):
        if utc is None:
            utc = a.now().utc_datetime()
        if isinstance(utc, str):
            utc      = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%S.%f%z")
        self.utc     = utc
        self.t       = a.ts.utc(utc)
        self.lat     = float(lat)
        self.lon     = float(lon)
        self.finder  = TimezoneFinder()
        self.tzName  = ''  # Compute the name on demand.
    
    def change_location(self, lat, lon):
        self.lat     = float(lat)
        self.lon     = float(lon)
        self.tzName  = ''  # Compute the name on demand.
    
    def change_time(self, utc):
        self.utc     = utc
        self.t       = a.ts.utc(utc)

    def getTimeZoneName(self):
        if '' == self.tzName:
            # Set tzName to string or None; do only once.
            tzName = self.finder.timezone_at(lat=self.lat, lng=self.lon)
            if tzName is None:
                # Per https://en.wikipedia.org/wiki/Tz_database#Area
                # Generic timezones are in the Etc/ Area, and have thier signs reversed.
                # zones west of GMT have a positive sign and those east have a negative
                # sign in their name (e.g "Etc/GMT-14" is 14 hours ahead of GMT).
                part = -int(self.lon/15)
                assert(-12 <= part <= 12)
                #print(self.lon, part)
                if not part:
                    tzName = 'Etc/GMT'
                else:
                    if part > 0:
                        tzName = 'Etc/GMT+' + str(part)
                    else:
                        tzName = 'Etc/GMT' + str(part)
            self.tzName = tzName
        return self.tzName

    def getDOY(self, dt):
        # Get the Day of Year of the datetime provided
        return dt.timetuple().tm_yday

    def getUtcTime(self):
        return self.utc

    def getLocalTime(self):
        tz = pytz.timezone(self.getTimeZoneName())
        return self.utc.astimezone(tz)

    def getJDate(self):
        return self.t._utc_float()

    def getGMST(self):
        # Greenwich Mean Sidereal Time
        return self.t.gmst

    def getLMST(self):
        # Local Mean Sidereal Time
        offset = self.lon * 24.0 / 360.0
        lmst = self.getGMST() + offset
        if lmst < 0.0: lmst = 24.0 + lmst
        return lmst

    def getLocalTimeOffset(self):
        # Get the difference between UTC al Local Time
        return float(self.getLocalTime().strftime('%z')) / 100.0

    def getEoT(self):
        # Get the Equation of Time; how many minutes ahead or behind mean time the Sun is
        LT   = self.getLocalTime()
        B    = radians((360.0 / 365.0) * ((self.getDOY(LT)) - 81))
        EoT  = (9.87 * sin(2 * B)) - (7.53 * cos(B)) - (1.5 * sin(B))
        return EoT

    def getEoT2(self):
        # From https://github.com/pvlib/pvlib-python/blob/master/pvlib/solarposition.py
        dayofyear = self.getDOY(self.getLocalTime())
        day_angle = (2. * pi / 365.) * (dayofyear - 1)
        eot = (1440.0 / 2 / pi) * (
            0.0000075 +
            0.001868 * cos(day_angle) - 0.032077 * sin(day_angle) -
            0.014615 * cos(2.0 * day_angle) - 0.040849 * sin(2.0 * day_angle)
        )
        return eot

    def getSolarTime(self):
        # Difference between local and solar time in minutes.
        # Depends on both location and day of year.
        # https://www.pveducation.org/pvcdrom/properties-of-sunlight/solar-time
        LT   = self.getLocalTime()
        TD   = int(self.lon * 24.0 / 360.0)
        LSTM = TD * 15.0
        EoT  = self.getEoT()
        TC   = 4 * (self.lon - LSTM) + EoT
        LST  = LT + timedelta(minutes=TC)
        if LT.dst().seconds != 0:
            LST -= timedelta(hours=1)
        return LST

    def decimalHoursToHMS(self, h):
        hour = int(h)
        min  = int((h - hour) * 60.0)
        sec  = int(((h - hour) - (min / 60.0)) * 3600.0)
        return '{0:02d}:{1:02d}:{2:02d}'.format(hour, min, sec)

    def print_report(self):
        print('UTC Time:   {0}'.format(self.getUtcTime()))
        print('Local Time: {0}'.format(self.getLocalTime()))
        print('Solar Time: {0}'.format(self.getSolarTime()))
        print('Time Zone:  {0}'.format(self.getTimeZoneName()))
        print('JDate:      {0}'.format(self.getJDate()))
        print('GMST:       {0}'.format(self.decimalHoursToHMS(tcalc.getGMST())))
        print('LMST:       {0}'.format(self.decimalHoursToHMS(tcalc.getLMST())))
        print('Local DOY:  {0}'.format(self.getDOY(tcalc.getLocalTime())))
        print('EoT:        {0}'.format(self.getEoT()))
        print('EoT2:       {0}'.format(self.getEoT2()))


if '__main__' == __name__:
    tcalc = TimeCalc(47.725316405, -122.180122359)
    tcalc.print_report()
    print()
    tcalc.change_location(-35, 150)
    tcalc.print_report()
