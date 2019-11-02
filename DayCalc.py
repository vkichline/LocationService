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
        if dt is None:
            self.DATE = a.time_to_local_datetime(a.now())
        else:
            self.DATE = dt # Local time, with time offset
        self.LAT  = latitude
        self.LON  = longitude
        self.ALT  = altitude
        self.topo = a.api.Topos(latitude, longitude, elevation_m=altitude)
        self.loc  = self.topo + a.earth
        self.clear_data()
        self.offset = int(self.DATE.strftime('%z')) / 100
        logging.debug('Offset: %s', self.offset)

    def clear_data(self):
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

    def change_date(self, datetime):
        self.DATE = datetime # Local time
        self.clear_data()

    def twilight(self, kind):
        if self.ASTRONOMICAL_TWILIGHT == kind:
            radius = 18.0
        elif self.NAUTICAL_TWILIGHT   == kind:
            radius = 12.0
        elif self.CIVIL_TWILIGHT      == kind:
            radius = 6.0
        else:
            raise IndexError()
        f_of_t    = a.risings_and_settings(a.planets, a.sun, self.loc, horizon=-0.3333, radius=radius)		
        day_start = self.DATE
        day_start = day_start.replace(hour=0, minute=0, second=0)
        day_end   = self.DATE
        day_end   = day_end.replace(hour=23, minute=59, second=59)
        return a.almanac.find_discrete(a.ts.utc(day_start), a.ts.utc(day_end), f_of_t)

    def culmination(self, body):
        # From https://github.com/skyfielders/python-skyfield/issues/243
        def f(t):
            alt, az, distance = self.loc.at(t).observe(body).apparent().altaz()
            return alt.degrees
        f.rough_period = 1.0
        t0  = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, -self.offset, 0, 0)
        t1  = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, 23-self.offset, 59, 59)
        try:
            times, maxima = a.almanac._find_maxima(t0, t1, f)
            t   = a.time_to_local_datetime(times[0])
            alt = maxima[0]
            return (t, alt)
        except:
            return None, None

    def rise_and_set(self, body):
        t0        = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, -self.offset, 0, 0)
        t1        = a.ts.utc(self.DATE.year, self.DATE.month, self.DATE.day, 23-self.offset, 59, 59)
        t, y      = a.almanac.find_discrete(t0, t1, a.risings_and_settings(a.planets, body, self.loc, radius=0.5))
        rise_time = set_time = None
        for yi, ti in zip(y, t):
            if yi:
                rise_time = a.time_to_local_datetime(ti)
            else:
                set_time  = a.time_to_local_datetime(ti)
        return rise_time, set_time

    def calc_all(self):
        times, kinds = self.twilight(self.ASTRONOMICAL_TWILIGHT)
        self.BMAT, self.EEAT    = a.time_to_local_datetime(times[0]), a.time_to_local_datetime(times[1])
        times, kinds = self.twilight(self.NAUTICAL_TWILIGHT)
        self.BMNT, self.EENT    = a.time_to_local_datetime(times[0]), a.time_to_local_datetime(times[1])
        times, kinds = self.twilight(self.CIVIL_TWILIGHT)
        self.BMCT, self.EECT    = a.time_to_local_datetime(times[0]), a.time_to_local_datetime(times[1])
        self.SCUL, self.SCALT   = self.culmination(a.sun)
        self.LCUL, self.LCALT   = self.culmination(a.moon)
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
        result['LAT']   = str(round(self.LAT, 5))
        result['LON']   = str(round(self.LON, 5))
        result['ALT']   = str(round(self.ALT, 1))
        result['BMAT']  = 'None' if self.BMAT is None else self.BMAT.strftime('%H:%M:%S')
        result['BMNT']  = 'None' if self.BMNT is None else self.BMNT.strftime('%H:%M:%S')
        result['BMCT']  = 'None' if self.BMCT is None else self.BMCT.strftime('%H:%M:%S')
        result['SRISE'] = 'None' if self.SRISE is None else self.SRISE.strftime('%H:%M:%S')
        result['SCUL']  = 'None' if self.SCUL is None else self.SCUL.strftime('%H:%M:%S')
        result['SCALT'] = str(round(self.SCALT, 2))
        result['SSET']  = 'None' if self.SSET is None else self.SSET.strftime('%H:%M:%S')
        result['EECT']  = 'None' if self.EECT is None else self.EECT.strftime('%H:%M:%S')
        result['EENT']  = 'None' if self.EENT is None else self.EENT.strftime('%H:%M:%S')
        result['EEAT']  = 'None' if self.EEAT is None else self.EEAT.strftime('%H:%M:%S')
        result['LPHA']  = str(round(self.LPHA, 1)) + '%'
        result['MRISE'] = 'None' if self.MRISE is None else self.MRISE.strftime('%H:%M:%S')
        result['LCUL']  = 'None' if self.LCUL is None else self.LCUL.strftime('%H:%M:%S')
        result['LCALT'] = str(round(self.LCALT, 2))
        result['MSET']  = 'None' if self.MSET is None else self.MSET.strftime('%H:%M:%S')
        return result

    def print_report(self):
        if not self.RDY:
            self.calc_all()
        print('Date                      ', self.DATE.date())
        print('Lat                       ', str(round(self.LAT, 5)))
        print('Lon                       ', str(round(self.LON, 5)))
        print('Alt                       ', str(round(self.ALT, 2)))
        print('Astronomical Dawn         ', self.BMAT.strftime('%H:%M:%S'))
        print('Nautical Dawn             ', self.BMNT.strftime('%H:%M:%S'))
        print('Civil Dawn                ', self.BMCT.strftime('%H:%M:%S'))
        print('Sunrise                   ', self.SRISE.strftime('%H:%M:%S'))
        print('Solar Noon Time           ', self.SCUL.strftime('%H:%M:%S'))
        print('Solar Noon Alt            ', round(self.SCALT, 2))
        print('Sunset                    ', self.SSET.strftime('%H:%M:%S'))
        print('End Civil Twilight        ', self.EECT.strftime('%H:%M:%S'))
        print('End Nautical Twilight     ', self.EENT.strftime('%H:%M:%S'))
        print('End Astronomical Twilight ', self.EEAT.strftime('%H:%M:%S'))
        print('Lunar illumination %      ', round(self.LPHA, 1))
        print('Moon Rise                 ', self.MRISE.strftime('%H:%M:%S'))
        print('Lunar Culmination         ', self.LCUL.strftime('%H:%M:%S'))
        print('Lunar Culmination Alt     ', round(self.LCALT, 2))
        print('Moon Set                  ', 'None' if self.MSET is None else self.MSET.strftime('%H:%M:%S'))

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
            'None' if self.BMAT  is None else self.BMAT.strftime('%H:%M:%S'),
            'None' if self.BMNT  is None else self.BMNT.strftime('%H:%M:%S'),
            'None' if self.BMCT  is None else self.BMCT.strftime('%H:%M:%S'),
            'None' if self.SRISE is None else self.SRISE.strftime('%H:%M:%S'),
            'None' if self.MSET  is None else self.MSET.strftime('%H:%M:%S'),
            0.0 if self.SCALT    is None else round(self.SCALT, 2),
            'None' if self.SSET  is None else self.SSET.strftime('%H:%M:%S'),
            'None' if self.EECT  is None else self.EECT.strftime('%H:%M:%S'),
            'None' if self.EENT  is None else self.EENT.strftime('%H:%M:%S'),
            'None' if self.EEAT  is None else self.EEAT.strftime('%H:%M:%S'),
            0.0 if self.LPHA     is None else round(self.LPHA, 1),
            'None' if self.MRISE is None else self.MRISE.strftime('%H:%M:%S'),
            'None' if self.LCUL  is None else self.LCUL.strftime('%H:%M:%S'),
            0.0 if self.LCALT    is None else round(self.LCALT, 2),
            'None' if self.MSET  is None else self.MSET.strftime('%H:%M:%S')
            ))

if '__main__' == __name__:
    t      = a.time_to_local_datetime(a.now())
    tester = DayCalc(a.home_topo.latitude.degrees, a.home_topo.longitude.degrees, a.home_topo.elevation.m, t)	
    tester.print_report()
