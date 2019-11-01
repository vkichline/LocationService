#!/usr/bin/env python3

import sys
sys.path.append('../')
import astro as a
from matplotlib import pyplot as plt

with a.loader.open(a.hipparcos.URL) as f:
    df = a.hipparcos.load_dataframe(f)

df = df[df['magnitude'] <= 4.0]
print('After filtering, there are {} stars'.format(len(df)))
bright_stars = a.Star.from_dataframe(df)
t = a.ts.now()
astrometric = a.earth.at(t).observe(bright_stars)
ra, dec, distance = astrometric.radec()

plt.scatter(ra.hours, dec.degrees, 8.1- df['magnitude']*2, 'k')
plt.xlim(7.0, 4.0)
plt.ylim(-20, 20)
plt.savefig('bright_stars.png')
