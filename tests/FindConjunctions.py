#!/usr/bin/env python3

# Given a UTC time, calculate the astrometric positions of all planets, sun and moon.
# Next, calculate the angular separations between each planet.
# Print an 10x10 grid of angular separations in decimal degrees.
#
# The data is calculated in this shape:
# 
# Pos | Separation angles
# --- | --------------------------------------------
# Su  | ->P  ->N  ->U  ->Sa ->J  ->Ma ->V  ->Me ->Mo
# Mo  | ->P  ->N  ->U  ->Sa ->J  ->Ma ->V  ->Me
# Me  | ->P  ->N  ->U  ->Sa ->J  ->Ma ->V
# V   | ->P  ->N  ->U  ->Sa ->J  ->Ma
# Ma  | ->P  ->N  ->U  ->Sa ->J
# J   | ->P  ->N  ->U  ->Sa
# Sa  | ->P  ->N  ->U
# U   | ->P  ->N
# N   | ->P
# P   |
#
# A function sep(body, body) will return the separation of any two body using the
# ragged array of calculations, and a 10x10 array of separation angles as floats
# will be created.
# The function render(10x10arry) will print the table to stdout.

import sys
sys.path.append('../')
import astro as a

MAX_SEP      = 0.5    # Maximum separation for a conjuntion in degrees (float)
PRINT_TABLES = False  # Print all calculations if True
DAYS_TO_CALC = 365    # How many days to calculate conjunctions for

# Indexes of the planets:
pSun         = 0
pMoon        = 1
pMercury     = 2
pVenus       = 3
pMars        = 4
pJupiter     = 5
pSaturn      = 6
pUranus      = 7
pNeptune     = 8
pPluto       = 9

# Indexes into the separations arrays:
sPluto       = 0
sNeptune     = 1
sUranus      = 2
sSaturn      = 3
sJupiter     = 4
sMars        = 5
sVenus       = 6
sMercury     = 7
sMoon        = 8
sSun         = 9


def planetFromIndex(index):
    """Given a pXXXX index, return a planet ephemeris."""
    planets = [a.sun, a.moon, a.mercury, a.venus, a.mars, a.jupiter, a.saturn, a.uranus, a.neptune, a.pluto]
    return planets[index]


def nameFromIndex(index):
    """Given a pXXXX index, return a planet name."""
    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    return planets[index]


class Separations:
    """Create an array of N separation calculations, indexed by sXXXX indexes."""
    def __init__(self, count):
        self.data = [None] * count
    def get(self, index):
        return self.data[index]
    def set(self, index, value):
        self.data[index] = value


class Calculations:
    """ The Calculations class represents one row of calculations:
        One Location object (the location of the planet) and 0 - 9
        angular separations, arranged by 'sXXXX' index order.
        All calculations are done at time t relative to earth.
        Radius is a float repesenting radius of the object."""
    def __init__(self, pIndex, sCount, radius, t):
        self.body        = planetFromIndex(pIndex)
        self.name        = nameFromIndex(pIndex)
        self.sCount      = sCount
        self.radius      = radius
        self.t           = t
        self.separations  = Separations(sCount)
        self.location    = a.earth.at(t).observe(self.body)
    def calc(self, cList):
        for sIndex in range(sPluto, self.sCount):
            target      = cList.calcs[pPluto-sIndex].body
            astrometric = a.earth.at(self.t).observe(target)
            sep         = self.location.separation_from(astrometric).degrees
            sep         -= cList.calcs[pPluto-sIndex].radius
            sep         -= self.radius
            self.separations.set(sIndex, abs(sep))
        # line = '{0:8s}'.format(self.name)
        # radec = self.location.radec(a.ts.J2000)
        # line += '{0:18s}'.format(str(radec[0]))
        # line += '{0:18s}'.format(str(radec[1]))
        # for i in range(0, self.sCount):
        #     line += '{0:8.4f}, '.format(self.separations.get(i))
        # print(line)
    def find_conjunctions(self, min_sep):
        """search for separations less than or equal to min_sep and return count and text"""
        text  = ''
        count = 0
        for sIndex in range(sPluto, self.sCount):
            sep = self.separations.get(sIndex)
            if sep <= min_sep:
                description = '{0} <-> {1}: '.format(self.name, nameFromIndex(pPluto-sIndex))
                text += '{0:21s} {1:.4f}\n'.format(description, self.separations.get(sIndex))
                count += 1
        return count, text


class CalculationList:
    """A list of 10 Calcuations objects, one for each planet."""
    def __init__(self, t):
        self.time = t
        self.calcs = []
        self.calcs.append(Calculations(pSun,     sSun,     0.25, t))
        self.calcs.append(Calculations(pMoon,    sMoon,    0.25, t))
        self.calcs.append(Calculations(pMercury, sMercury, 0.0,  t))
        self.calcs.append(Calculations(pVenus,   sVenus,   0.0,  t))
        self.calcs.append(Calculations(pMars,    sMars,    0.0,  t))
        self.calcs.append(Calculations(pJupiter, sJupiter, 0.0,  t))
        self.calcs.append(Calculations(pSaturn,  sSaturn,  0.0,  t))
        self.calcs.append(Calculations(pUranus,  sUranus,  0.0,  t))
        self.calcs.append(Calculations(pNeptune, sNeptune, 0.0,  t))
        self.calcs.append(Calculations(pPluto,   sPluto,   0.0,  t))
    def calc(self):
        for row in self.calcs:
            row.calc(self)
    def get_location(self, pIndex):
        return self.calcs[pIndex].location
    def get_separation(self, p1, p2):
        i1 = min(p1, p2)
        i2 = pPluto - max(p1, p2)
        row = self.calcs[i1]
        sep = row.separations.get(i2)
        return '{0:8.4f}  '.format(sep)
    def find_conjunctions(self, min_sep):
        count = 0
        text  = ''
        for row in self.calcs:
            c1, t1 = row.find_conjunctions(min_sep)
            count += c1
            text  += t1
        if count > 0:
            if not PRINT_TABLES:
                text = '{0}\n'.format(self.time.utc_datetime()) + text
        return count, text


def calculate_all(t):
    table = CalculationList(t)
    table.calc()
    if PRINT_TABLES:
        print(t.utc_datetime())
        header = 'Body       Right Ascension  Declination      '
        for pIndex in range(pSun, pPluto+1):
            name = nameFromIndex(pIndex)
            header += name.center(8) + '  '
        separator = '----       ---------------  ---------------  '
        for pIndex in range(pSun, pPluto+1):
            separator += '--------  '
        
        print(header)
        print(separator)

        for pIndex in range(pSun, pPluto):
            pos   = table.get_location(pIndex)
            radec = pos.radec(a.ts.J2000)
            line  = '{0:10s} {1:15s} {2:15s}  '.format(nameFromIndex(pIndex), str(radec[0]), str(radec[1]))
            for p2 in range(pSun, pPluto):
                if pIndex == p2:
                    line += ' ' * 10
                else:
                    line += table.get_separation(pIndex, p2)
            print(line)
        print()

    count, text = table.find_conjunctions(MAX_SEP)
    if 0 < count:
        if PRINT_TABLES:
            print('Conjunctions:')
        print(text)
    return count


if '__main__' == __name__:
    y = 2019
    m = 10
    d = 17
    h = 12
    m = 0
    s = 0
    x = DAYS_TO_CALC   # How many days to calculate

    conj_count = 0
    for i in range(0, x):
        t = a.ts.utc(y, m, d+i, h, m, s)
        conj_count += calculate_all(t)
    if 0 < conj_count:
        print('Total conjunctions:   {0}'.format(conj_count))
