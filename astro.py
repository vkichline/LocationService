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
# astro.this_year()    Integer for this year (local time)
# astro.this_month()   Integer for this month (local time)
# astro.this_day()     Integer for this day (local time)
# astro.year_start()   Time object for the first moment of this local year, converted to UTC
# astro.year_end()     Time object for the last moment of this local year, converted to UTC
# astro.month_start()  Time object for the first moment of this local month, converted to UTC
# astro.month_end()    Time object for the last moment of this local month, converted to UTC
# astro.day_start()    Time object for the first moment of this local day, converted to UTC
# astro.day_noon()     Time object for noon of this local day, converted to UTC
# astro.day_end()      Time object for the last moment of this local day, converted to UTC
# astro.format_dt(dt)  Format a DateTime object consistangly; date, then time.
# astro.topo_from_data(lat, lon, alt) Get a Topo object set to the current GPS location
# astro.loc_from_data(lat, lon, alt)  Get a Location object set to the current GPS location on the surface of the Earth
# astro.name_from_body(body)          Given one of the planet objects above, return its name
# astro.body_from_name(name)          Given a name, return the exact object from api (eaiser to compare than planet[name])
# astro.time_to_local_datetime(Time)  Convert Time object to a datetime in local timezone (no timezone info)
# astro.pos_to_consteallation(pos)    Given a position, return a short string for the contellation name
# astro.info(target, obsv, pos_only=False, T=now)  Return a dictionary of info about the body's pos, rise/set, etc. in local time
# astro.print_planets(obsv, pos_only=False, T=Now) Print out an ephemeris, short or long
# astro.risings_and_settings(ephemeris, target, topos, horizon, radius)  Calc rise/set for any body


import math
from skyfield import api, almanac
from skyfield.api import Star
from skyfield.data import hipparcos
from skyfield.nutationlib import iau2000b
from datetime import datetime, timezone


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
    topos_at = (observer).at
    h = horizon - radius

    def is_body_up_at(t):
        t._nutation_angles = iau2000b(t.tt)
        return topos_at(t).observe(target).apparent().altaz()[0].degrees > h
    is_body_up_at.rough_period = 0.5  # twice a day
    return is_body_up_at


def time_to_local_datetime(t):
    utc_time = t.utc_datetime()
    local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
    return local_time


# Observe a target body from an obsv body or Topo and return info.
# If pos_only is omitted or False, return:
# name, alt, azm, dist, rising, setting, illum, const for a target body
# alt and azm are in decimal degrees
# distance is in miles, rise and set are datetime's in local time.
# illum is in percentage
# const is a string abbreviation.
#
# If pos_only is True, a much faster calculation is performed and returns:
# name, alt, azm, dist, illum
#
# If t is a skyfield Time object, use that for calcuation. If t is None, use now()/
#
def info(target, obsv, pos_only=False, t=None):
    ROUNDING = 3
    if t is None:    t = now()
    name           = name_from_body(target)
    astrometric    = obsv.at(t).observe(target)
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
    t, y = almanac.find_discrete(day_start(), day_end(),
                                 risings_and_settings(planets, target, obsv, radius=rad))
    for yi, ti in zip(y, t):
        if yi:
            rise_time = ti
        else:
            set_time = ti
    rise_time = time_to_local_datetime(rise_time)
    set_time  = time_to_local_datetime(set_time)
    return name, alt, azm, dist, rise_time, set_time, illum, const


# Given an obsv body or Topo (example: home_pos), print an ephemeris to stdout. If pos_only, then just alt, azm and distance are printed.
# If not pos_only (the default) all info from astro.info is included.
# Special allowances are made for Sun and Moon.
# If t is a skyfield Time object, use that for calcuation. If t is None, use now()
#
def print_planets(obsv, pos_only=False, t=None):
    if t is None:
        t = now()
    def print_title(pos_only):
        dt = time_to_local_datetime(t)
        print('%s for lat %.4f lon %.4f at %s local time.' %
              ('Fast data' if pos_only else 'Data', home_topo.latitude.degrees, home_topo.longitude.degrees, dt.strftime('%H:%M:%S')))
    def print_header(pos_only):
        if pos_only:
            print('Body       Alt     Azm      Distance')
            print('-------  ------  ------  -------------')
        else:
            print('Body       Alt     Azm   Const   Rising   Setting   Illum     Distance')
            print('-------  ------  ------  -----  --------  --------  -----  -------------')
    def print_body(body, pos_only):
        if pos_only:
            name, alt, azm, dist, illum = info(body, obsv, True, t)
            print('{0:7s}  {1:6.2f}  {2:6.2f}  {3:13,}'.format(name, alt, azm, int(dist)))
        else:
            name, alt, azm, dist, rise_time, set_time, illum, const = info(body, obsv, False, t)
            if illum is None:
                illum = 100.0
            print('{0:7s}  {1:6.2f}  {2:6.2f}  {3:5s}  {4:8s}  {5:8s}  {6:5.1f}  {7:13,}'.format(name, alt, azm, const, rise_time.strftime('%H:%M:%S'), set_time.strftime('%H:%M:%S'), illum, int(dist)))
    print_title(pos_only)
    print_header(pos_only)
    for body in [sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto]:
        print_body(body, pos_only)


def now():
    return ts.now()


def this_year():
    now = datetime.now()
    return now.year


def this_month():
    now = datetime.now()
    return now.month


def this_day():
    now = datetime.now()
    return now.day


def year_start():
    return ts.utc(datetime(this_year(), 1, 1, 0, 0, 0).astimezone(tz=timezone.utc))


def year_end():
    return ts.utc(datetime(this_year(), 12, 31, 23, 59, 59).astimezone(tz=timezone.utc))


def month_start():
    return ts.utc(datetime(this_year(), this_month(), 1, 0, 0, 0).astimezone(tz=timezone.utc))


def month_end():
    return ts.utc(datetime(this_year(), this_month(), 31, 23, 59, 59).astimezone(tz=timezone.utc))


def day_start():
    return ts.utc(datetime(this_year(), this_month(), this_day(), 0, 0, 0).astimezone(tz=timezone.utc))


def day_noon():
    return ts.utc(datetime(this_year(), this_month(), this_day(), 12, 0, 0).astimezone(tz=timezone.utc))


def day_end():
    return ts.utc(datetime(this_year(), this_month(), this_day(), 23, 59, 59).astimezone(tz=timezone.utc))


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
