import math
import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)
NC, NR = 23, 20

def line_mask(path, thr=190):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im, dtype=np.int16)
    return (a.min(axis=2) >= thr), a

def centers(R, x0, y0):
    dx, dy = 1.5 * R, SQ3 * R
    cs = []
    for c in range(NC):
        for r in range(NR):
            cs.append((x0 + c * dx, y0 + r * dy + (c % 2) * dy / 2.0))
    return np.array(cs)

def score(mask, R, x0, y0):
    H, W = mask.shape
    cs = centers(R, x0, y0)
    d = 0.866 * R
    hits = 0
    tot = 0
    for k in range(6):
        a = math.radians(30 + 60 * k)
        sx = np.round(cs[:, 0] + d * math.cos(a)).astype(int)
        sy = np.round(cs[:, 1] + d * math.sin(a)).astype(int)
        ok = (sx >= 2) & (sx < W - 2) & (sy >= 2) & (sy < H - 2)
        s = sx[ok]; t = sy[ok]
        sub = mask[t - 2:t + 3, s - 2:s + 3] if False else None
        vals = np.zeros(len(s), dtype=bool)
        for o in (-2, 0, 2):
            for o2 in (-2, 0, 2):
                vals |= mask[t + o2, s + o]
        hits += int(vals.sum())
        tot += len(s)
    return hits / tot

def fit(path):
    mask, _ = line_mask(path)
    best = None
    for R in range(92, 106):
        for x0 in range(320, 470, 5):
            for y0 in range(30, 230, 5):
                s = score(mask, R, x0, y0)
                if best is None or s > best[0]:
                    best = (s, R, x0, y0)
    # refine
    s, R, x0, y0 = best
    for R2 in range(R - 2, R + 3):
        for x2 in range(x0 - 6, x0 + 7, 1):
            for y2 in range(y0 - 6, y0 + 7, 1):
                v = score(mask, R2, x2, y2)
                if v > best[0]:
                    best = (v, R2, x2, y2)
    return best

for p in ('map1.jpg', 'map2.jpg'):
    s, R, x0, y0 = fit(p)
    print(p, round(s, 4), 'R=', R, 'x0=', x0, 'y0=', y0)
