"""Locate every flat hex edge (horizontal white run) to pin down x0 and y0.

A flat-top hex of radius R has a top/bottom edge of length R centred on its
column's x.  Detecting those runs gives the column x-positions and the row
boundary y-positions directly.
"""
import math
from collections import defaultdict
import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)
R = 106.0
DX = 1.5 * R
DY = SQ3 * R

for name in ('map1.jpg', 'map2.jpg'):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    H, W = A.shape[:2]
    runs = []
    for y in range(H):
        row = white[y]
        x = 0
        while x < W:
            if row[x]:
                s = x
                while x < W and row[x]:
                    x += 1
                if x - s >= 90:
                    runs.append((y, (s + x - 1) / 2.0, x - s))
            else:
                x += 1
    # cluster runs by (y, x)
    byx = defaultdict(list)
    for y, cx, ln in runs:
        key = round(cx / 5) * 5
        byx[key].append(y)
    print(name, 'H=', H, 'runs=', len(runs))
    # group y values per x cluster
    cols = {}
    for key, ys in byx.items():
        ys = sorted(ys)
        groups = []
        for y in ys:
            if groups and y == groups[-1][-1] + 1:
                groups[-1].append(y)
            else:
                groups.append([y])
        cols[key] = [sum(g) / len(g) for g in groups]
    xs = sorted(cols)
    print('  x clusters with >=6 edges:', [x for x in xs if len(cols[x]) >= 6][:25])
    for x in xs:
        if len(cols[x]) >= 6:
            print('    x=%s edges=%s' % (x, [round(v, 1) for v in cols[x]]))
    print()
