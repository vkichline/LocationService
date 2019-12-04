#!/usr/bin/env python3

# DayCalc is a class which calculates daylight and darkness information
# about a given day, at a specific position and altitude.
# Calculations are expensive, so they are not performed on creation.
# Dawn and dusk pairs are created together; all calculations can be
# preformed asynchronously by callin calc_all().
# Van Kichline, October 2019
#
# DayCalc.RDY is True when all data is available.
#
# Proposed data:
# LAT	Latitude
# LON	Longitude
# ALT	Altitude
# DATE	Date
# BMAT	Beginning of Astronomical Dawn
# BMNT	Beginning of Nautical Dawn
# BMCT	Beginning of Civil Dawn
# SRISE	Moment of Sunrise
# SRAZM	Azimuth of Sunrise
# SCUL	Moment of Solar Culmination
# SCALT	Altitude of Culmination
# SSET	Moment of Sunset
# SSAZM	Azimuth of Sunset
# EECT	End of Civil Dusk
# EENT	End of Nautical Dusk
# EEAT	End of Astronomical Dusk
# LDL	Length of Daylight
# SDIA	Angular size of Sun at Culmination
# LPHA	Moon Phase/illumination
# MRISE	Moon Rise
# MRAZM	Azimuth at Moonrise
# LCUL	Lunar Culmination
# LCALT	Altitude of Lunar Culmination
# ?	(Is there any kind of Lunar twilight?)
# MSET	Moon Set
# MSAZM	Azimuth of Moonset
# LML	Length of Moonlight
# LDIA	Angular size of Moon at Culmination
# DARKT	Length of darkness (No Moon or Twilight)
# BDARK	Beginning of Darkness
# EDARK	End of Darkness
# SDIST Approximate distance to the sun
# LDIST Approximate distance to the moon

import astro as a
from datetime import datetime, timedelta
from pytz import timezone
import logging, json

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


class DayCalc:
    ASTRONOMICAL_TWILIGHT = 0
    NAUTICAL_TWILIGHT     = 1
    CIVIL_TWILIGHT        = 2

    def __init__(self, latitude, longitude, altitude=0, dt=None):
        logging.debug('DayCalc ctor: %s, %s, %s, %s', latitude, longitude, altitude, dt)
        logging.debug('%s, %s, %s, %s', type(latitude), type(longitude), type(altitude), type(dt))
        self.topo = a.api.Topos(latitude, longitude, elevation_m=altitude)
        self.loc  = a.earth + self.topo
        if dt is None:
            self.DATE = a.time_to_local_datetime(a.now(), self.loc)
        else:
            self.DATE = dt # Local time, with time offset
        self.LAT  = latitude
        self.LON  = longitude
        self.ALT  = altitude
        self.init_data()

    def init_data(self):
        self.BMAT  = None,
        self.BMNT  = None
        self.BMCT  = None
        self.SRISE = None
        self.SCUL  = None
        self.SCALT = None
        self.SSET  = None
        self.EECT  = None
        self.EENT  = None
        self.EEAT  = None
        self.LPHA  = None
        self.MRISE = None
        self.LCUL  = None
        self.LCALT = None
        self.MSET  = None
        self.RDY   = False
        self.calc_offset()

    def change_date(self, datetime):
        self.DATE = datetime # Local time
        self.init_data()
    
    def calc_offset(self):
        ta = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, 0, 0, 0)
        tl = a.time_to_local_datetime(ta, self.loc)
        self.offset = 24 - tl.hour
        logging.debug('Offset: %s', self.offset)

    def twilight(self, kind):
        if kind == self.ASTRONOMICAL_TWILIGHT:
            radius = 18.0
        elif kind == self.NAUTICAL_TWILIGHT:
            radius = 12.0
        elif kind == self.CIVIL_TWILIGHT:
            radius = 6.0
        else:
            raise IndexError()
        f_of_t    = a.risings_and_settings(a.planets, a.sun, self.loc, horizon=-0.3333, radius=radius)		
        day_start = self.DATE
        day_start = day_start.replace(hour=0, minute=0, second=0)
        day_end   = self.DATE
        day_end   = day_end.replace(hour=23, minute=59, second=59)
        return a.almanac.find_discrete(a.ts.utc(day_start), a.ts.utc(day_end), f_of_t)

    def rise_and_set(self, body):
        t0        = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, + self.offset, 0, 0)
        t1        = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, 23 + self.offset, 59, 59)
        t, y      = a.almanac.find_discrete(t0, t1, a.risings_and_settings(a.planets, body, self.loc, radius=0.5))
        rise_time = set_time = None
        assert(0 == a.time_to_local_datetime(t0, self.loc).time().hour)
        for yi, ti in zip(y, t):
            if yi:
                rise_time = a.time_to_local_datetime(ti, self.loc)
            else:
                set_time  = a.time_to_local_datetime(ti, self.loc)
        # Because of the moon's apparent motion, there are some times it may not rise or set in a given
        if body == a.moon and not rise_time:
            t0    = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, + self.offset - 2, 0, 0)
            t, y  = a.almanac.find_discrete(t0, t1, a.risings_and_settings(a.planets, a.moon, self.loc, radius=0.5))
            t = t[0] if y[0] else t[1]
            rise_time = a.time_to_local_datetime(t, self.loc)
        elif body == a.moon and not set_time:
            t1    = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, 23 + self.offset + 2, 59, 59)
            t, y  = a.almanac.find_discrete(t0, t1, a.risings_and_settings(a.planets, a.moon, self.loc, radius=0.5))
            t = t[0] if y[1] else t[1]
            set_time = a.time_to_local_datetime(t, self.loc)
        return rise_time, set_time

    def calc_all(self):
        times, _kinds = self.twilight(self.ASTRONOMICAL_TWILIGHT)
        self.BMAT, self.EEAT    = a.time_to_local_datetime(times[0], self.loc), a.time_to_local_datetime(times[1], self.loc)
        times, _kinds = self.twilight(self.NAUTICAL_TWILIGHT)
        self.BMNT, self.EENT    = a.time_to_local_datetime(times[0], self.loc), a.time_to_local_datetime(times[1], self.loc)
        times, _kinds = self.twilight(self.CIVIL_TWILIGHT)
        self.BMCT, self.EECT    = a.time_to_local_datetime(times[0], self.loc), a.time_to_local_datetime(times[1], self.loc)
        self.SCUL, self.SCALT   = a.culmination(a.sun,  self.loc, a.ts.utc(self.DATE))
        self.LCUL, self.LCALT   = a.culmination(a.moon, self.loc, a.ts.utc(self.DATE))
        self.SRISE, self.SSET   = self.rise_and_set(a.sun)
        self.MRISE, self.MSET   = self.rise_and_set(a.moon)
        self.LPHA               = a.almanac.fraction_illuminated(a.planets, 'moon', a.ts.utc(self.DATE)) * 100.0
        self.RDY                = True

    def as_json(self):
        d = self.as_dict()
        return json.dumps(d)

    def as_dict(self):
        if not self.RDY:
            self.calc_all()
        result = {}
        result['DATE']  = str(self.DATE.date())
        result['LAT']   = round(self.LAT, 5)
        result['LON']   = round(self.LON, 5)
        result['ALT']   = round(self.ALT, 1)
        result['BMAT']  = '' if self.BMAT is None else self.BMAT.strftime('%H:%M:%S')
        result['BMNT']  = '' if self.BMNT is None else self.BMNT.strftime('%H:%M:%S')
        result['BMCT']  = '' if self.BMCT is None else self.BMCT.strftime('%H:%M:%S')
        result['SRISE'] = '' if self.SRISE is None else self.SRISE.strftime('%H:%M:%S')
        result['SCUL']  = '' if self.SCUL is None else self.SCUL.strftime('%H:%M:%S')
        result['SCALT'] = round(self.SCALT, 2)
        result['SSET']  = '' if self.SSET is None else self.SSET.strftime('%H:%M:%S')
        result['EECT']  = '' if self.EECT is None else self.EECT.strftime('%H:%M:%S')
        result['EENT']  = '' if self.EENT is None else self.EENT.strftime('%H:%M:%S')
        result['EEAT']  = '' if self.EEAT is None else self.EEAT.strftime('%H:%M:%S')
        result['LPHA']  = round(self.LPHA, 1)
        result['MRISE'] = '' if self.MRISE is None else self.MRISE.strftime('%H:%M:%S')
        result['LCUL']  = '' if self.LCUL is None else self.LCUL.strftime('%H:%M:%S')
        result['LCALT'] = 0.0 if self.LCALT is None else round(self.LCALT, 2)
        result['MSET']  = '' if self.MSET is None else self.MSET.strftime('%H:%M:%S')
        return result

    def print_report(self):
        if not self.RDY:
            self.calc_all()
        print('Date                      ', self.DATE.date())
        print('Lat                       ', str(round(self.LAT, 5)))
        print('Lon                       ', str(round(self.LON, 5)))
        print('Alt                       ', str(round(self.ALT, 2)))
        print('Astronomical Dawn         ', '' if self.BMAT is None else self.BMAT.strftime('%H:%M:%S'))
        print('Nautical Dawn             ', '' if self.BMNT is None else self.BMNT.strftime('%H:%M:%S'))
        print('Civil Dawn                ', '' if self.BMCT is None else self.BMCT.strftime('%H:%M:%S'))
        print('Sunrise                   ', '' if self.SRISE is None else self.SRISE.strftime('%H:%M:%S'))
        print('Solar Noon Time           ', '' if self.SCUL is None else self.SCUL.strftime('%H:%M:%S'))
        print('Solar Noon Alt            ', round(self.SCALT, 2))
        print('Sunset                    ', '' if self.SSET is None else self.SSET.strftime('%H:%M:%S'))
        print('End Civil Twilight        ', '' if self.EECT is None else self.EECT.strftime('%H:%M:%S'))
        print('End Nautical Twilight     ', '' if self.EENT is None else self.EENT.strftime('%H:%M:%S'))
        print('End Astronomical Twilight ', '' if self.EEAT is None else self.EEAT.strftime('%H:%M:%S'))
        print('Lunar illumination %      ', round(self.LPHA, 1))
        print('Moon Rise                 ', '' if self.MRISE is None else self.MRISE.strftime('%H:%M:%S'))
        print('Lunar Culmination         ', '' if self.LCUL is None else self.LCUL.strftime('%H:%M:%S'))
        print('Lunar Culmination Alt     ', 0.0 if self.LCALT is None else round(self.LCALT, 2))
        print('Moon Set                  ', '' if self.MSET is None else self.MSET.strftime('%H:%M:%S'))

    def print_report_header(self, fixed = True):
        print('For latitude {0}, longitude {1}, at {2} meters:'.format(self.LAT, self.LON, self.ALT))
        if fixed:
            print('Date        AstDawn   NautDawn  CivDawn   SunRise   SolNoon   NoonAlt  SunSet    CivTwi    NautTwi   AstTwi    Illm%  MoonRise  MoonCulm  CulmAlt  MoonSet')
            print('----------  --------  --------  --------  --------  --------  -------  --------  --------  --------  --------  -----  --------  --------  -------  --------')
        else:
            print('Date\tAstDawn\tNautDawn\tCivDawn\tSunRise\tSolNoon\tNoonAlt\tSunSet\tCivTwi\tNautTwi\tAstTwi\tIllm%\tMoonRise\tMoonCulm\tCulmAlt\tMoonSet')

    def print_report_footer(self):
        print('----------  --------  --------  --------  --------  --------  -------  --------  --------  --------  --------  -----  --------  --------  -------  --------')
        print('Date        AstDawn   NautDawn  CivDawn   SunRise   SolNoon   NoonAlt  SunSet    CivTwi    NautTwi   AstTwi    Illm%  MoonRise  MoonCulm  CulmAlt  MoonSet')

    def print_report_row(self, fixed = True):
        if not self.RDY:
            self.calc_all()
        fixed_format  = '{0}  {1:8s}  {2:8s}  {3:8s}  {4:8s}  {5:8s}  {6:7.2f}  {7:8s}  {8:8s}  {9:8s}  {10:8s}  {11:5.1f}  {12:8s}  {13:8s} {14:8.1f}  {15:8s}'
        tabbed_format = '{0}\t{1:s}\t{2:s}\t{3:s}\t{4:s}\t{5:s}\t{6:7.2f}\t{7:s}\t{8:s}\t{9:s}\t{10:s}\t{11:5.1f}\t{12:s}\t{13:s}\t{14:8.1f}\t{15:s}'
        fmt = fixed_format if fixed else tabbed_format
        print(fmt.format(
            self.DATE.date(),
            '' if self.BMAT  is None else self.BMAT.strftime('%H:%M:%S'),
            '' if self.BMNT  is None else self.BMNT.strftime('%H:%M:%S'),
            '' if self.BMCT  is None else self.BMCT.strftime('%H:%M:%S'),
            '' if self.SRISE is None else self.SRISE.strftime('%H:%M:%S'),
            '' if self.SCUL  is None else self.SCUL.strftime('%H:%M:%S'),
            0.0 if self.SCALT    is None else round(self.SCALT, 2),
            '' if self.SSET  is None else self.SSET.strftime('%H:%M:%S'),
            '' if self.EECT  is None else self.EECT.strftime('%H:%M:%S'),
            '' if self.EENT  is None else self.EENT.strftime('%H:%M:%S'),
            '' if self.EEAT  is None else self.EEAT.strftime('%H:%M:%S'),
            0.0 if self.LPHA     is None else round(self.LPHA, 1),
            '' if self.MRISE is None else self.MRISE.strftime('%H:%M:%S'),
            '' if self.LCUL  is None else self.LCUL.strftime('%H:%M:%S'),
            0.0 if self.LCALT    is None else round(self.LCALT, 2),
            '' if self.MSET  is None else self.MSET.strftime('%H:%M:%S')
        ))

if '__main__' == __name__:
    lat, lon = a.lat_lon_from_observer(a.home_loc)
    t      = a.time_to_local_datetime(a.now(), a.home_loc)
    tester = DayCalc(lat, lon, a.home_topo.elevation.m, t)	
    tester.print_report()
