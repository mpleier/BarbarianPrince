"""Locate the printed 4-digit hex labels and compare their centroids with the
model hex centres.  This is an independent check of x0 / y0 for both scans."""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, NR, R, DX, DY, SCANS, hex_id

for name, first_row in (('map1.jpg', 1), ('map2.jpg', 13)):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = A.min(axis=2) > 205
    lab, n = ndimage.label(white)
    objs = ndimage.find_objects(lab)
    p = SCANS[name]
    found = []
    for idx, sl in enumerate(objs, start=1):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        area = (lab[sl] == idx).sum()
        if 12 <= h <= 30 and 25 <= w <= 70 and area >= 120:
            cy = (sl[0].start + sl[0].stop) / 2.0
            cx = (sl[1].start + sl[1].stop) / 2.0
            col = round((cx - p['x0']) / DX) + 1
            row = round((cy - p['y0'] - (col - 1) % 2 * DY / 2.0) / DY) + first_row
            if 1 <= col <= NC and first_row <= row <= first_row + 9:
                found.append((col, row, cx, cy))
    print('=== %s : %d label-like blobs' % (name, len(found)))
    ex, ey = [], []
    for col, row, cx, cy in found:
        mx, my = p['x0'] + DX * (col - 1), p['y0'] + DY * (row - first_row) + (col - 1) % 2 * DY / 2.0
        ex.append(cx - mx)
        ey.append(cy - my)
    if ex:
        print('   dx: mean %+.2f  min %+.2f  max %+.2f' % (np.mean(ex), min(ex), max(ex)))
        print('   dy: mean %+.2f  min %+.2f  max %+.2f' % (np.mean(ey), min(ey), max(ey)))
