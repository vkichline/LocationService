#!/usr/bin/env python3

# As a module:
# Loads ephemeris and timescale remotely or locally, but ignore out-of-date reloads.
# This can be used to download all files while online, then loading them reliably offline.
# Using this file ensures sharing a common location for data with consistant variable names.
#
# As a program:
# Loads files, but downloads replacements fir out of date files, and exits.
#
# Usage:
# import astro
#
# Requires:
# numpy, skyfield, pandas
#
# This loads data and makes the following properties available:
# astro.api            SkyField api object
# astro.almanac        Skyfield almanac object
# astro.loader         Catalog loader with common position set
# astro.ts             Time scale
# astro.planets        de421.bsp Ephemeris
# astro.sun            Ephemeris of the Sun
# astro.moon           Ephemeris of the Moon
# astro.mercury        Ephemeris of Mercury
# astro.venus          Ephemeris of Venus
# astro.earth          Ephemeris of Earth
# astro.mars           Ephemeris of Mars
# astro.jupiter        Ephemeris of Jupiter
# astro.saturn         Ephemeris of Saturn
# astro.uranus         Ephemeris of Uranus
# astro.neptune        Ephemeris of Neptune
# astro.pluto          Ephemeris of Pluto
# astro.data_dir       Location of skyfield data files
# astro.home_topo      Topocentric location of my house (without earth vector)
# astro.home_loc       Topocentric location of my house (with earth vector added)
# astro.now()          Time object represeting moment the function is called
# astro.year_start(t)  Time object for the first moment of the year of the time provided
# astro.year_end(t)    Time object for the last moment of the year of the time provided
# astro.month_start(t) Time object for the first moment of the month of the time provided
# astro.month_end(t)   Time object for the last moment of the month of the time provided
# astro.day_start(t)   Time object for the first moment of the day of the time provided
# astro.day_noon(t)    Time object for noon of of the time provided
# astro.day_end(t)     Time object for the last moment of of the time provided
# astro.format_dt(dt)  Format a DateTime object consistangly; date, then time.
# astro.topo_from_data(lat, lon, alt) Get a Topo object set to the current GPS location
# astro.loc_from_data(lat, lon, alt)  Get a Location object set to the current GPS location on the surface of the Earth
# astro.name_from_body(body)          Given one of the planet objects above, return its name
# astro.body_from_name(name)          Given a name, return the exact object from api (eaiser to compare than planet[name])
# astro.time_to_local_datetime(Time)  Convert Time object to a datetime in local timezone (no timezone info)
# astro.pos_to_consteallation(pos)    Given a position, return a short string for the contellation name
# astro.info(target, observer, pos_only=False, T=now)  Return a dictionary of info about the body's pos, rise/set, etc. in local time
# astro.print_planets(observer, pos_only=False, T=Now) Print out an ephemeris, short or long
# astro.risings_and_settings(ephemeris, target, topos, horizon, radius)  Calc rise/set for any body


import math, calendar
from skyfield import api, almanac
from skyfield.api import Star
from skyfield.data import hipparcos
from skyfield.nutationlib import iau2000b
from datetime import datetime, timezone, timedelta


LOAD_HIPPARCOS  = False  # TODO: Should be a function of cmd line param
data_dir        = '/usr/local/share/skyfield/data'


def name_from_body(body):
    if (sun      == body): return 'Sun'
    elif(moon    == body): return 'Moon'
    elif(mercury == body): return 'Mercury'
    elif(venus   == body): return 'Venus'
    elif(earth   == body): return 'Earth'
    elif(mars    == body): return 'Mars'
    elif(jupiter == body): return 'Jupiter'
    elif(saturn  == body): return 'Saturn'
    elif(uranus  == body): return 'Uranus'
    elif(neptune == body): return 'Neptune'
    elif(pluto   == body): return 'Pluto'
    else:                  return 'Unknown'


def body_from_name(name):
    if not isinstance(name, str): return None
    name = name.lower()
    if ('sun'      == name): return sun
    elif('moon'    == name): return moon
    elif('mercury' == name): return mercury
    elif('venus'   == name): return venus
    elif('earth'   == name): return earth
    elif('mars'    == name): return mars
    elif('jupiter' == name): return jupiter
    elif('saturn'  == name): return saturn
    elif('uranus'  == name): return uranus
    elif('neptune' == name): return neptune
    elif('pluto'   == name): return pluto
    else:                    return None


def pos_to_constellation(pos):
    constellation_at = api.load_constellation_map()
    return constellation_at(pos)


# From: https://github.com/skyfielders/python-skyfield/blob/master/skyfield/almanac.py
def risings_and_settings(ephemeris, target, observer, horizon=-0.3333, radius=0):
    h = horizon - radius
    def is_body_up_at(t):
        t._nutation_angles = iau2000b(t.tt)
        return observer.at(t).observe(target).apparent().altaz()[0].degrees > h
    is_body_up_at.rough_period = 0.5  # twice a day
    return is_body_up_at


# From https://github.com/skyfielders/python-skyfield/issues/243
def culmination(body, obsverver, t):
    def f(t):
        alt, _az, _distance = obsverver.at(t).observe(body).apparent().altaz()
        return alt.degrees
    f.rough_period = 1.0

    dt   = t.utc_datetime()
    # Determine time offset for the day (TODO: may be 1 hour off on DST change dates)
    ta = ts.utc(dt.year, dt.month, dt.day, 0, 0, 0)
    tl = time_to_local_datetime(ta)
    offset = 24 - tl.hour

    t0   = ts.utc(dt.year, dt.month, dt.day,  offset,  0,  0)
    t1   = ts.utc(dt.year, dt.month, dt.day, 23 + offset, 59, 59)
    assert(0 == time_to_local_datetime(t0).time().hour)
    try:
        times, maxima = almanac._find_maxima(t0, t1, f, epsilon=0.000001) # tuned to avoid exceptions
        t   = time_to_local_datetime(times[0])
        alt = maxima[0]
        return (t, alt)
    except:
        return None, None


def time_to_local_datetime(t):
    utc_time = t.utc_datetime()
    local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
    return local_time


# Observe a target body from an observer body or Topo and return info.
# If pos_only is omitted or False, return:
# name, alt, azm, dist, rising, culmination, setting, culmatl, illum, const for a target body
# alt, azm and culmalt are in decimal degrees
# distance is in miles, rise, culmination and set are datetime's in local time.
# illum is in percentage
# const is a string abbreviation.
#
# If pos_only is True, a much faster calculation is performed and returns:
# name, alt, azm, dist, illum
#
# If t is a skyfield Time object, use that for calcuation. If t is None, use now()/
#
def info(target, observer, pos_only=False, t=None):
    ROUNDING = 3
    if t is None:    t = now()
    name           = name_from_body(target)
    astrometric    = observer.at(t).observe(target)
    apparent       = astrometric.apparent()
    const          = pos_to_constellation(apparent)
    alt, azm, dist = apparent.altaz('standard')
    alt            = round(alt.degrees, ROUNDING)
    azm            = round(azm.degrees, ROUNDING)
    dist           = round(dist.km * 0.6213712, ROUNDING)
    if target in [moon, mercury, venus, mars]:
        illum = almanac.fraction_illuminated(planets, name, t)
        if math.isnan(illum):
            illum = 1.0
        illum *= 100.0
    else:
        illum = None
    if pos_only:
        return name, alt, azm, dist, illum

    if target == moon or target == sun:
        rad = 0.5
    else:
        rad = 0.0
    
    ta, ya = almanac.find_discrete(
                day_start(t),
                day_end(t),
                risings_and_settings(planets, target, observer, radius=rad))
    culm_time, culm_alt = culmination(target, observer, t)
    rise_time = set_time = None
    for yi, ti in zip(ya, ta):
        if yi:
            rise_time = ti
        else:
            set_time = ti
    rise_time = None if rise_time is None else time_to_local_datetime(rise_time)
    set_time  = None if set_time  is None else time_to_local_datetime(set_time)
    return name, alt, azm, dist, rise_time, culm_time, set_time, culm_alt, illum, const


# Given an observer body or Topo (example: home_pos), print an ephemeris to stdout.
# If pos_only, then just alt, azm and distance are printed.
# If not pos_only (the default) all info from astro.info is included.
# Special allowances are made for Sun and Moon.
# If t is a skyfield Time object, use that for calcuation. If t is None, use now()
#
def print_planets(observer, pos_only=False, t=None):
    if t is None:
        t = now()
    def print_title(pos_only):
        dt = time_to_local_datetime(t)
        print('%s for %s from latitude %.4f, longitude %.4f at %s local time.' % (
            'Fast data' if pos_only else 'Data',
            time_to_local_datetime(t).date(),
            home_topo.latitude.degrees,
            home_topo.longitude.degrees,
            dt.strftime('%H:%M:%S')))
    def print_header(pos_only):
        if pos_only:
            print('Body       Alt     Azm      Distance')
            print('-------  ------  ------  -------------')
        else:
            print('Body       Alt     Azm   Const   Rising    Culmin   Setting    CulAlt  Illum     Distance')
            print('-------  ------  ------  -----  --------  --------  --------   ------  -----  -------------')
    def print_body(body, pos_only):
        if pos_only:
            name, alt, azm, dist, illum = info(body, observer, True, t)
            print('{0:7s}  {1:6.2f}  {2:6.2f}  {3:13,}'.format(
                name,
                alt,
                azm,
                int(dist)
            ))
        else:
            name, alt, azm, dist, rise_time, culm_time, set_time, culm_alt, illum, const = info(body, observer, False, t)
            if illum is None:
                illum = 100.0
            print('{0:7s}  {1:6.2f}  {2:6.2f}  {3:5s}  {4:8s}  {5:8s}  {6:8s}  {7:7.2f}  {8:5.1f}  {9:13,}'.format(
                name,
                alt,
                azm,
                const,
                '' if rise_time is None else rise_time.strftime('%H:%M:%S'),
                '' if culm_time is None else culm_time.strftime('%H:%M:%S'),
                '' if set_time  is None else set_time.strftime('%H:%M:%S'),
                0.0 if culm_alt is  None else culm_alt,
                illum,
                int(dist)
            ))
    print_title(pos_only)
    print_header(pos_only)
    for body in [sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto]:
        print_body(body, pos_only)


def now():
    return ts.now()


def year_start(t):
    dt = time_to_local_datetime(t)
    dt = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return ts.utc(dt)


def year_end(t):
    dt = time_to_local_datetime(t)
    dt = dt.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    return ts.utc(dt)


def month_start(t):
    dt = time_to_local_datetime(t)
    dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return ts.utc(dt)


def month_end(t):
    dt = time_to_local_datetime(t)
    md = [31, 28, 31, 30, 31, 31, 30, 31, 30, 31, 30, 31]
    if calendar.isleap(dt.year): md[1] += 1
    ld = md[dt.month]
    dt = dt.replace(day=ld, hour=23, minute=59, second=59, microsecond=999999)
    return ts.utc(dt)


def day_start(t):
    dt = time_to_local_datetime(t)
    dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return ts.utc(dt)

def day_noon(t):
    dt = time_to_local_datetime(t)
    dt = dt.replace(hour=12, minute=0, second=0, microsecond=0)
    return ts.utc(dt)


def day_end(t):
    dt = time_to_local_datetime(t)
    dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return ts.utc(dt)


def format_dt(dt):
    return dt.strftime('%m/%d/%Y %H:%M:%S')


def topo_from_data(lat, lon, alt):
    return api.Topos(lat, lon, elevation_m=alt)


def loc_from_data(lat, lon, alt):
    topo = topo_from_data(lat, lon, alt)
    return earth + topo


if '__main__' == __name__:
    print('Loading timescale.')
    loader = api.Loader(data_dir, expire=True, verbose=True)
    data_downloaded = True
    # This is quite intense on a RPi Zero, should be a cmd line flag:
    if LOAD_HIPPARCOS:
        with loader.open(hipparcos.URL) as f:
            print('Loading Hipparcos catalog')
            df = hipparcos.load_dataframe(f)
    print(loader.log)
else:
    # verbose displays progress bar when downloading
    loader = api.Loader(data_dir, expire=False, verbose=False)


try:
    ts    = loader.timescale()
except:
    print('Error loading timescale. Falling back on builtin timescale.')
    ts    = loader.timescale(builtin=True)
planets   = loader('de421.bsp')
sun       = planets['sun']
moon      = planets['moon']
mercury   = planets['mercury']
venus     = planets['venus']
earth     = planets['earth']
mars      = planets['mars']
jupiter   = planets['jupiter barycenter']
saturn    = planets['saturn barycenter']
uranus    = planets['uranus barycenter']
neptune   = planets['neptune barycenter']
pluto     = planets['pluto barycenter']
home_topo = api.Topos('47.725476 N', '122.1802654 W', elevation_m=95)
home_loc  = earth + home_topo


if '__main__' == __name__:
    print_planets(home_loc)
