"""Fine lattice fit per scan, restricted to a clean interior window."""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

def fit(A, cols, rows, R, x0r, y0r, tol=5):
    white = (A.min(axis=2) > 200)
    dist = distance_transform_edt(~white)
    H, W = A.shape[:2]
    DX, DY = 1.5 * R, math.sqrt(3) * R
    best = None
    for x0 in x0r:
        for y0 in y0r:
            tot = hit = 0
            for c in cols:
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

R = 106.0
A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)

print('map1 window:', fit(A1, range(2, 20), range(2, 12), R, range(350, 430, 2), range(70, 130, 2)))
print('map2 window:', fit(A2, range(2, 20), range(14, 23), R, range(350, 430, 2), range(80, 240, 2)))
