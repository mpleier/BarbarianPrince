"""Compare a handful of candidate origins using mean edge-to-white distance."""
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

SQ3 = math.sqrt(3.0)
R = 106.0
DX, DY = 1.5 * R, SQ3 * R

def md(A, cols, rows, x0, y0):
    dist = distance_transform_edt(~(A.min(axis=2) > 200))
    H, W = A.shape[:2]
    ds = []
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
    return round(float(np.mean(ds)), 3)

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
for x0, y0 in [(377, 94), (377, 96), (377, 98), (377, 99), (378, 98), (379, 98), (380, 98)]:
    print('map1 (%d,%d) mean dist = %s' % (x0, y0, md(A1, range(1, 21), range(1, 13), x0, y0)))
print()
for x0, y0 in [(377, 198), (377, 200), (377, 203), (378, 203), (379, 203), (378, 200)]:
    print('map2 (%d,%d) mean dist = %s' % (x0, y0, md(A2, range(1, 21), range(13, 24), x0, y0)))
