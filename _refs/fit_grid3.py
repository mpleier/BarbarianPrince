import math
import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)

def line_mask(path, thr=185):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im, dtype=np.int16)
    return (a.min(axis=2) >= thr)

def score(mask, R, x0, y0, nc, nr):
    H, W = mask.shape
    dx, dy = 1.5 * R, SQ3 * R
    cs = np.array([(x0 + c * dx, y0 + r * dy + (c % 2) * dy / 2.0)
                   for c in range(nc) for r in range(nr)])
    d = 0.866 * R
    hits = tot = 0
    for k in range(6):
        a = math.radians(30 + 60 * k)
        sx = np.round(cs[:, 0] + d * math.cos(a)).astype(int)
        sy = np.round(cs[:, 1] + d * math.sin(a)).astype(int)
        ok = (sx >= 2) & (sx < W - 2) & (sy >= 2) & (sy < H - 2)
        s, t = sx[ok], sy[ok]
        vals = np.zeros(len(s), dtype=bool)
        for o in (-2, 0, 2):
            for o2 in (-2, 0, 2):
                vals |= mask[t + o2, s + o]
        hits += int(vals.sum()); tot += len(s)
    return hits / tot

def fit(path, nc, nr):
    mask = line_mask(path)
    H, W = mask.shape
    best = None
    for R in range(85, 116):
        for x0 in range(320, 440, 4):
            for y0 in range(10, 260, 4):
                s = score(mask, R, x0, y0, nc, nr)
                if best is None or s > best[0]:
                    best = (s, R, x0, y0)
    s, R, x0, y0 = best
    for R2 in range(R - 3, R + 4):
        for x2 in range(x0 - 8, x0 + 9):
            for y2 in range(y0 - 8, y0 + 9):
                v = score(mask, R2, x2, y2, nc, nr)
                if v > best[0]:
                    best = (v, R2, x2, y2)
    return best

print('map1 (23 cols x 12 rows):', fit('map1.jpg', 23, 12))
print('map2 (23 cols x  8 rows):', fit('map2.jpg', 23, 8))
