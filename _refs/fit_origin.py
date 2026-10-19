"""Refine the lattice origin for each scan at R = 106."""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

R = 106.0
DX, DY = 1.5 * R, math.sqrt(3) * R

def score(A, nc, rows, tol=4):
    white = (A.min(axis=2) > 200)
    dist = distance_transform_edt(~white)
    H, W = A.shape[:2]
    best = None
    for x0 in range(340, 420, 4):
        for y0 in range(60, 130, 4):
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
            s = hit / tot if tot else 0
            if best is None or s > best[0]:
                best = (round(s, 4), x0, y0)
    return best

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
print('map1 fine:', score(A1, 20, list(range(1, 13))))
print('map2 fine:', score(A2, 20, list(range(13, 24))))
