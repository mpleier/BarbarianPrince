"""Print mean colour of the top rows of map2 and the bottom rows of map1."""
import numpy as np
from PIL import Image

for name, rows in (('map1.jpg', range(2090, 2136)), ('map2.jpg', range(0, 60))):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.float32)
    band = A[:, 250:1100]
    print('===', name)
    for y in rows:
        r, g, b = band[y].mean(axis=0)
        print('  y=%4d  mean RGB = (%.0f, %.0f, %.0f)' % (y, r, g, b))
