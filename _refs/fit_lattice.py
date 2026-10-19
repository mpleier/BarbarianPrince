"""Fit the hex lattice by scoring how well hex edges land on white grid lines."""
import math
import numpy as np
from PIL import Image

def score(A, R, x0, y0, nc=20, nr=12, first_row=1):
    H, W = A.shape[:2]
    DX, DY = 1.5 * R, math.sqrt(3) * R
    tot = hit = 0
    for c in range(1, nc + 1):
        for r in range(first_row, first_row + nr):
            cx = x0 + DX * (c - 1)
            cy = y0 + DY * (r - first_row) + (c % 2) * DY / 2
            if cx - R < 0 or cx + R > W:
                continue
            for a in range(0, 360, 60):
                p1 = (cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
                p2 = (cx + R * math.cos(math.radians(a + 60)), cy + R * math.sin(math.radians(a + 60)))
                for t in np.linspace(0.1, 0.9, 9):
                    x = int(round(p1[0] + t * (p2[0] - p1[0]))); y = int(round(p1[1] + t * (p2[1] - p1[1])))
                    if 0 <= x < W and 0 <= y < H:
                        tot += 1
                        if A[y, x].min() > 200:
                            hit += 1
    return hit / tot if tot else 0

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
best = None
for R in range(85, 115):
    for x0 in range(330, 430, 10):
        for y0 in range(60, 130, 10):
            s = score(A1, R, x0, y0)
            if best is None or s > best[0]:
                best = (s, R, x0, y0)
print('best map1:', best)
