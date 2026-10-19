"""Overlay the model hex outlines on crops at the left and right board edges."""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import R, DX, DY, SCANS, board_xy, board_corners

im = Image.open('_refs/map1.jpg').convert('RGB')
A = np.asarray(im, dtype=np.int16)

# locate the printed horizontal grid lines in the column-1 band
sub = A[:, 324:431].min(axis=2) > 200
frac = sub.mean(axis=1)
ys, i, n = [], 0, len(frac)
while i < n:
    if frac[i] > 0.5:
        j = i
        while j + 1 < n and frac[j + 1] > 0.5:
            j += 1
        ys.append((i + j) / 2.0)
        i = j + 1
    else:
        i += 1
print('detected grid lines in map1 column-1 band:', [round(v, 1) for v in ys])

for tag, x0, x1 in (('left', 150, 700), ('right', 3100, 3508)):
    crop = im.crop((x0, 1800, x1, 2250)).copy()
    d = ImageDraw.Draw(crop)
    for c in range(1, 21):
        for r in range(10, 13):
            pts = board_corners(c, r)
            pts = [(px - x0, py - 1800) for px, py in pts]
            if any(-50 < px < (x1 - x0) + 50 for px, py in pts):
                d.line(pts + pts[0:1], fill=(255, 0, 0), width=2)
    crop.save('_refs/edge_%s.png' % tag)
    print('wrote _refs/edge_%s.png' % tag)
