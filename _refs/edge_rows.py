"""Print the exact flat-edge run centres along a few known boundary rows."""
import numpy as np
from PIL import Image

for name, ys in (('map1.jpg', [190, 373, 557, 741, 924, 1106, 1290, 1473, 1657, 1842, 2027]),
                 ('map2.jpg', [111, 297, 482, 666, 850, 1034, 1218, 1402, 1586, 1770, 1954, 2134])):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    print(name)
    for y in ys:
        band = white[max(0, y - 2):y + 3].all(axis=0)
        runs = []
        x = 0
        W = len(band)
        while x < W:
            if band[x]:
                s = x
                while x < W and band[x]:
                    x += 1
                if x - s >= 80:
                    runs.append((round((s + x - 1) / 2, 1), x - s))
            else:
                x += 1
        print('  y=%4d centres=%s' % (y, runs))
    print()
