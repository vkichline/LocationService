import sys
sys.path.append('../')
import astro as a

a.loader.verbose = True
a.loader('de405.bsp')
a.loader('de406.bsp')
a.loader('de422.bsp')
a.loader('de430t.bsp')
a.loader('jup310.bsp')
