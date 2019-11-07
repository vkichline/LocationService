#!/usr/bin/env python3

import sys
sys.path.append('../')
import astro as a

j = a.whats_up(a.home_loc, a.now())
print(j)