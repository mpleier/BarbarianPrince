"""Detect the printed horizontal grid lines in several column bands of each scan."""
import math
import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)
R = 106.0
DY = SQ3 * R
DX = 1.5 * R


def lines(mask, cx, half=35, thresh=0.9):
    band = mask[:, int(cx - half):int(cx + half)]
    frac = band.mean(axis=1)
    out, y, H = [], 0, len(frac)
    while y < H:
        if frac[y] > thresh:
            s = y
            while y < H and frac[y] > thresh:
                y += 1
            out.append((s + y - 1) / 2.0)
        else:
            y += 1
    return out


for name, x0, y0, first in (('map1.jpg', 377.0, 98.2, 1),
                            ('map2.jpg', 377.0, 203.3, 13)):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    mask = A.min(axis=2) > 200
    print('===', name)
    for c in (1, 2, 3, 4):
        cx = x0 + DX * (c - 1)
        got = lines(mask, cx)
        pred = [y0 + DY * (r - first) + ((c - 1) % 2) * DY / 2.0 - DY / 2.0
                for r in range(first, first + 12)]
        print(' col %d  detected %s' % (c, [round(v, 1) for v in got[:6]]))
        print(' col %d  predicted %s' % (c, [round(v, 1) for v in pred[:6]]))
        if got and pred:
            print('   first-line delta = %.2f' % (got[0] - pred[0]))
    print()
