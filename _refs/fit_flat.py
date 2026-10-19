"""Mean distance for the FLAT (horizontal) edges only - the cleanest signal."""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

SQ3 = math.sqrt(3.0)
R = 106.0
DX, DY = 1.5 * R, SQ3 * R

def flat_md(A, cols, rows, x0, y0, R):
    dist = distance_transform_edt(~(A.min(axis=2) > 200))
    H, W = A.shape[:2]
    DXl, DYl = 1.5 * R, SQ3 * R
    ds = []
    for c in cols:
        for r in rows:
            cx = x0 + DXl * (c - 1)
            cy = y0 + DYl * (r - rows[0]) + ((c - 1) % 2) * DYl / 2
            if cx - R < 0 or cx + R > W or cy - R < 0 or cy + R > H:
                continue
            for sgn in (-1, 1):
                yy = cy + sgn * SQ3 * R / 2
                for t in np.linspace(0.1, 0.9, 9):
                    x = int(round(cx - R / 2 + t * R))
                    y = int(round(yy))
                    if 0 <= x < W and 0 <= y < H:
                        ds.append(dist[y, x])
    return round(float(np.mean(ds)), 3)

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
print('map1 flat-edge fit:')
for y0 in range(92, 104):
    print('   y0=%d -> %s' % (y0, flat_md(A1, range(1, 21), range(1, 13), 377, y0, R)))
print('map2 flat-edge fit:')
for y0 in range(196, 208):
    print('   y0=%d -> %s' % (y0, flat_md(A2, range(1, 21), range(13, 24), 377, y0, R)))
print('radius check (map1, y0=98):')
for rr in (104, 105, 106, 107, 108):
    print('   R=%d -> %s' % (rr, flat_md(A1, range(1, 21), range(1, 13), 377, 98, rr)))
