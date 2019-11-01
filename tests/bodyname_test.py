#!/usr/bin/env python3

import sys
sys.path.append('../')
import astro as a

m = 'Moon'
target = a.body_from_name(m)
print(target)
obsv = a.home_loc
print(obsv)
name, alt, azm, dist, illum = a.info(target, obsv, True)
print(name, alt, azm, dist, illum)

print('Testing empty string')
target = a.body_from_name('')
print(target)
print('Testing None')
target = a.body_from_name(None)
print(target)
print('Testing foobar')
target = a.body_from_name('foobar')
print(target)
