"""Print every white run on a row where all odd columns have flat edges."""
import numpy as np
from PIL import Image

for name, ys in (('map1.jpg', [190, 374, 558, 741, 924]),
                 ('map2.jpg', [111, 297, 482, 666, 850])):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    print(name)
    for y in ys:
        row = white[y]
        runs = []
        x = 0
        W = len(row)
        while x < W:
            if row[x]:
                s = x
                while x < W and row[x]:
                    x += 1
                if x - s >= 60:
                    runs.append((s, x - 1, x - s))
            else:
                x += 1
        print('  y=%4d runs=%s' % (y, runs))
    print()
