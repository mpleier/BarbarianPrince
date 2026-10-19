"""Measure the printed flat-edge width (== R) and the column pitch (== DX)."""
import numpy as np
from PIL import Image

for name, ys in (('map1.jpg', [190, 374, 558, 742, 924, 1107, 1291, 1474, 1658, 1842, 2027]),
                 ('map2.jpg', [111, 297, 483, 667, 851, 1035, 1219, 1402, 1586, 1771, 1955])):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    print(name)
    for y in ys:
        row = white[y]
        # find the run containing x=377
        if not row[377]:
            print('   y=%4d  no line at x=377' % y)
            continue
        s = 377
        while s > 0 and row[s - 1]:
            s -= 1
        e = 377
        while e < len(row) - 1 and row[e + 1]:
            e += 1
        print('   y=%4d  run %d..%d  width=%d  centre=%.1f' % (y, s, e, e - s + 1, (s + e) / 2))
    print()
