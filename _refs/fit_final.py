"""Precise lattice fit with the SAME parity convention as src/geometry.py.

geometry.py: cx = x0 + DX*(col-1); cy = y0 + DY*(row-first_row) + ((col-1)%2)*DY/2
"""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

SQ3 = math.sqrt(3.0)
R = 106.0
DX = 1.5 * R
DY = SQ3 * R

def fit(A, cols, rows, x0r, y0r, tol=5):
    white = (A.min(axis=2) > 200)
    dist = distance_transform_edt(~white)
    H, W = A.shape[:2]
    best = None
    for x0 in x0r:
        for y0 in y0r:
            tot = hit = 0
            for c in cols:
                for r in rows:
                    cx = x0 + DX * (c - 1)
                    cy = y0 + DY * (r - rows[0]) + ((c - 1) % 2) * DY / 2
                    if cx - R < 0 or cx + R > W or cy - R < 0 or cy + R > H:
                        continue
                    for a in range(0, 360, 60):
                        p1 = (cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
                        p2 = (cx + R * math.cos(math.radians(a + 60)), cy + R * math.sin(math.radians(a + 60)))
                        for t in np.linspace(0.15, 0.85, 7):
                            x = int(round(p1[0] + t * (p2[0] - p1[0])))
                            y = int(round(p1[1] + t * (p2[1] - p1[1])))
                            if 0 <= x < W and 0 <= y < H:
                                tot += 1
                                if dist[y, x] <= tol:
                                    hit += 1
            s = hit / tot if tot else 0
            if best is None or s > best[0]:
                best = (round(s, 4), round(x0, 1), round(y0, 1))
    return best

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
print('map1:', fit(A1, range(1, 21), range(1, 13), range(360, 400, 2), range(90, 110, 1)))
print('map2:', fit(A2, range(1, 21), range(13, 24), range(360, 400, 2), range(195, 215, 1)))
