"""Fit the hex lattice using a distance transform from the white grid lines."""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

def fit(A, nc, nr, first_row, Rrange, x0range, y0range, tol=4):
    white = (A.min(axis=2) > 200)
    dist = distance_transform_edt(~white)
    H, W = A.shape[:2]
    best = None
    for R in Rrange:
        DX, DY = 1.5 * R, math.sqrt(3) * R
        for x0 in x0range:
            for y0 in y0range:
                tot = hit = 0
                for c in range(1, nc + 1):
                    for r in range(first_row, first_row + nr):
                        cx = x0 + DX * (c - 1)
                        cy = y0 + DY * (r - first_row) + (c % 2) * DY / 2
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
                    best = (round(s, 4), R, x0, y0)
    return best

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
print('map1:', fit(A1, 20, 12, 1, range(88, 112, 2), range(330, 430, 10), range(40, 140, 10)))
print('map2:', fit(A2, 20, 11, 13, range(88, 112, 2), range(330, 430, 10), range(40, 140, 10)))
