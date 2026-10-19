"""Final lattice calibration: robust fit of the printed grid lines.

Convention used by src/geometry.py (flat-top hexes, column 1 is the anchor):
    centre(1, r) = (x0, y0 + DY * (r - first_row))
    flat edges of that hex are at centre_y +/- DY/2

So in the column-1 band the printed horizontal lines are
    map1:  y = y0_1 + DY * (k - 1) + DY/2      k = 1 .. 12   (k/k+1 boundary)
    map2:  y = y0_2 + DY * (k - 13) - DY/2    k = 13 .. 24  (top edge of row k)

Terrain artwork creates false positives, so y0 is chosen by RANSAC: the value
that makes the most detected lines land on the lattice.
"""
import math
import os

import numpy as np
from PIL import Image

R = 106.0
SQ3 = math.sqrt(3.0)
DY = SQ3 * R
DX = 1.5 * R
NC, NR = 20, 23
BAND = (324, 431)          # column-1 flat edge: x = 377 +/- 53


def candidates(path, band=BAND):
    A = np.asarray(Image.open(path).convert('RGB'), dtype=np.int16)
    white = A.min(axis=2) > 200
    frac = white[:, band[0]:band[1]].mean(axis=1)
    out = []
    y = 0
    while y < A.shape[0]:
        if frac[y] > 0.5:
            y0 = y
            acc = 0.0
            cnt = 0
            while y < A.shape[0] and frac[y] > 0.5:
                acc += frac[y]
                cnt += 1
                y += 1
            out.append((y0 + y - 1) / 2.0)
        else:
            y += 1
    return out


def fit(path, first_row, n_lines, sign):
    """sign = +1: line = y0 + DY*(k-1) + DY/2 ;  sign = -1: line = y0 + DY*(k-1) - DY/2"""
    ys = candidates(path)
    best = None
    for g in ys:
        y0 = g - sign * DY / 2.0
        hits = []
        for y in ys:
            k = round((y - y0 - sign * DY / 2.0) / DY) + 1
            if 1 <= k <= n_lines:
                err = y - (y0 + DY * (k - 1) + sign * DY / 2.0)
                if abs(err) <= 2.5:
                    hits.append((k, y))
        if best is None or len(hits) > len(best[1]):
            best = (y0, hits)
    hits = best[1]
    y0 = float(np.mean([y - DY * (k - 1) - sign * DY / 2.0 for k, y in hits]))
    print('  %s: %d of %d lattice lines matched' % (os.path.basename(path), len(hits), n_lines))
    for k, y in hits:
        pred = y0 + DY * (k - 1) + sign * DY / 2.0
        print('     line %2d  printed %7.1f  model %7.1f  err %+5.2f' % (k, y, pred, y - pred))
    resid = [y - (y0 + DY * (k - 1) + sign * DY / 2.0) for k, y in hits]
    pitch = (hits[-1][1] - hits[0][1]) / (hits[-1][0] - hits[0][0])
    return y0, max(abs(r) for r in resid), pitch


print('R = %.1f  DX = %.3f  DY = %.3f' % (R, DX, DY))
y0_1, w1, p1 = fit('_refs/map1.jpg', 1, 12, +1)
print('  -> y0(map1) = %.2f   max residual %.2f   measured pitch %.2f (R=%.2f)'
      % (y0_1, w1, p1, p1 / SQ3))
y0_2, w2, p2 = fit('_refs/map2.jpg', 13, 12, -1)
print('  -> y0(map2) = %.2f   max residual %.2f   measured pitch %.2f (R=%.2f)'
      % (y0_2, w2, p2, p2 / SQ3))
print()
print('map1 last printed line (12/13 boundary) = %.1f' % (y0_1 + DY * 11 + DY / 2))
print('map2 first printed line (12/13 boundary) = %.1f' % (y0_2 - DY / 2))
print('=> stitch offset BOARD_Y_OFF(map2) = %.2f'
      % ((y0_1 + DY * 11 + DY / 2) - (y0_2 - DY / 2)))
print()
print('board extents (hex lattice, unified frame):')
print('  left   x = %.1f' % (377.0 - R))
print('  right  x = %.1f' % (377.0 + DX * (NC - 1) + R))
print('  top    y = %.1f' % (y0_1 - DY / 2))
print('  bottom y = %.1f' % (y0_1 + DY * (NR - 1) + DY / 2))
print('scan sizes: map1 3510x2136, map2 3510x2148')


