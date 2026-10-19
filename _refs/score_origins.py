"""Score specific candidate origins so the current SCANS values can be judged."""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

R = 106.0
DX, DY = 1.5 * R, math.sqrt(3) * R

def score(A, nc, rows, x0, y0, tol=4):
    white = (A.min(axis=2) > 200)
    dist = distance_transform_edt(~white)
    H, W = A.shape[:2]
    tot = hit = 0
    for c in range(1, nc + 1):
        for r in rows:
            cx = x0 + DX * (c - 1)
            cy = y0 + DY * (r - rows[0]) + (c % 2) * DY / 2
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
    return round(hit / tot, 4) if tot else 0

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
for x0 in (377, 384, 391, 398):
    for y0 in (96, 104, 112, 120):
        print('map1 x0=%d y0=%d -> %s' % (x0, y0, score(A1, 20, list(range(1, 13)), x0, y0)))
print()
for x0 in (377, 384, 391, 398):
    for y0 in (199, 107, 112, 119):
        print('map2 x0=%d y0=%d -> %s' % (x0, y0, score(A2, 20, list(range(13, 24)), x0, y0)))
