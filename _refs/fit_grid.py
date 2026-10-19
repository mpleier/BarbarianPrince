"""Fit the flat-top hex lattice of a map scan by maximising white-line coverage."""
from PIL import Image
import numpy as np
import math
import itertools
import sys

def score(a, R, x0, y0, cmax, rmax):
    H, W, _ = a.shape
    DX = 1.5 * R
    DY = math.sqrt(3) * R
    tot = 0.0
    hit = 0
    for c in range(cmax):
        for r in range(rmax):
            cx = x0 + DX * c
            cy = y0 + DY * r + (DY / 2 if c % 2 else 0)
            if cy - R < 0 or cy + R > H or cx + R > W:
                continue
            for k in range(6):
                ang = math.radians(60 * k)
                p1 = (cx + R * math.cos(ang), cy + R * math.sin(ang))
                p2 = (cx + R * math.cos(ang + math.pi / 3), cy + R * math.sin(ang + math.pi / 3))
                n = 12
                for t in range(1, n):
                    x = int(round(p1[0] + (p2[0] - p1[0]) * t / n))
                    y = int(round(p1[1] + (p2[1] - p1[1]) * t / n))
                    if 0 <= x < W and 0 <= y < H:
                        tot += 1
                        if a[y, x, 0] > 225 and a[y, x, 1] > 225 and a[y, x, 2] > 225:
                            hit += 1
    return hit / tot if tot else 0

def fit(path, cmax, rmax, Rrange, x0range, y0range):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    best = None
    for R in Rrange:
        for x0 in x0range:
            for y0 in y0range:
                s = score(a, R, x0, y0, cmax, rmax)
                if best is None or s > best[0]:
                    best = (s, R, x0, y0)
    return best

if __name__ == "__main__":
    print("map1", fit("_refs/map1.jpg", 20, 12, range(95, 116, 2), range(350, 421, 10), range(100, 181, 10)))
    print("map2", fit("_refs/map2.jpg", 20, 11, range(95, 116, 2), range(350, 421, 10), range(180, 261, 10)))