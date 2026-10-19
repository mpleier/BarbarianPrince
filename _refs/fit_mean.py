"""Minimise the MEAN distance from hex edges to the nearest white grid line."""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

SQ3 = math.sqrt(3.0)

def mean_dist(A, cols, rows, R, x0, y0):
    white = (A.min(axis=2) > 200)
    dist = distance_transform_edt(~white)
    DX, DY = 1.5 * R, SQ3 * R
    ds = []
    H, W = A.shape[:2]
    for c in cols:
        for r in rows:
            cx = x0 + DX * (c - 1)
            cy = y0 + DY * (r - rows[0]) + ((c - 1) % 2) * DY / 2
            if cx - R < 0 or cx + R > W or cy - R < 0 or cy + R > H:
                continue
            for a in range(0, 360, 60):
                p1 = (cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
                p2 = (cx + R * math.cos(math.radians(a + 60)), cy + R * math.sin(math.radians(a + 60)))
                for t in np.linspace(0.2, 0.8, 6):
                    x = int(round(p1[0] + t * (p2[0] - p1[0])))
                    y = int(round(p1[1] + t * (p2[1] - p1[1])))
                    if 0 <= x < W and 0 <= y < H:
                        ds.append(dist[y, x])
    return float(np.mean(ds))

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)

best1 = best2 = None
for R in (104.0, 105.0, 106.0, 107.0, 108.0):
    for x0 in range(372, 392, 2):
        for y0 in range(88, 108, 2):
            v = mean_dist(A1, range(1, 21), range(1, 13), R, x0, y0)
            if best1 is None or v < best1[0]:
                best1 = (round(v, 3), R, x0, y0)
    for x0 in range(372, 392, 2):
        for y0 in range(192, 212, 2):
            v = mean_dist(A2, range(1, 21), range(13, 24), R, x0, y0)
            if best2 is None or v < best2[0]:
                best2 = (round(v, 3), R, x0, y0)
print('map1 best:', best1)
print('map2 best:', best2)
