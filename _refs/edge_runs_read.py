"""Print the white runs on a few clean horizontal grid lines so the flat-edge
x-positions can be read off directly."""
import numpy as np
from PIL import Image

for name, lines in (('map1.jpg', [190.5, 373.5, 557.5, 741.0, 924.5, 1106.5,
                                   1290.5, 1473.5, 1657.5, 1842.0, 2027.5]),
                    ('map2.jpg', [111.5, 297.0, 482.5, 666.5, 850.5, 1034.5,
                                  1218.5, 1402.0, 1586.0, 1770.5, 1955.0])):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    print('===', name)
    for y in lines:
        row = A[int(y) - 2:int(y) + 3].min(axis=2).mean(axis=0)
        white = row > 200
        runs, start = [], None
        for x, w in enumerate(white):
            if w and start is None:
                start = x
            elif not w and start is not None:
                if x - start >= 60:
                    runs.append((start, x - 1))
                start = None
        if start is not None and len(white) - start >= 60:
            runs.append((start, len(white) - 1))
        print('  y=%6.1f : %s' % (y, '  '.join('%d-%d' % r for r in runs)))
