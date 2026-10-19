"""Decisive check: for column 1 only, how far are the predicted flat edges
from the actual white grid lines?"""
import math
import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)
R = 106.0
DY = SQ3 * R

for name, rows, lo, hi in (('map1.jpg', range(1, 13), 94, 102),
                          ('map2.jpg', range(13, 24), 203, 213)):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    H = A.shape[0]
    print(name)
    for y0 in range(lo, hi + 1):
        errs = []
        for r in rows:
            cy = y0 + DY * (r - rows[0])
            for sgn in (-1, 1):
                yy = int(round(cy + sgn * SQ3 * R / 2))
                if 0 <= yy < H:
                    band = white[max(0, yy - 8):yy + 9, 340:410]
                    idx = np.where(band.any(axis=1))[0]
                    if len(idx):
                        errs.append(min(abs(i - (yy - max(0, yy - 8))) for i in idx))
                    else:
                        errs.append(9)
        print('   y0=%d  mean err=%.2f  max err=%d' % (y0, np.mean(errs), max(errs)))
    print()
