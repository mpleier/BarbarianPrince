"""Cluster hex interior colours to derive terrain for every hex on the map."""
from PIL import Image
import numpy as np
import math
import json

R = 105.7
DX = 1.5 * R
DY = math.sqrt(3) * R

def interior(path, c, r, yoff, r0):
    a = np.array(Image.open(path).convert("RGB")).astype(float)
    H, W, _ = a.shape
    x = 380 + DX * (c - 1)
    y = yoff + DY * (r - r0) + (DY / 2 if c % 2 == 0 else 0)
    rad = 0.62 * R
    yy0, yy1 = int(y - rad), int(y + rad) + 1
    xx0, xx1 = int(x - rad), int(x + rad) + 1
    yy0 = max(yy0, 0); yy1 = min(yy1, H)
    xx0 = max(xx0, 0); xx1 = min(xx1, W)
    p = a[yy0:yy1, xx0:xx1]
    # keep only pixels inside the hexagon
    ys, xs = np.mgrid[yy0:yy1, xx0:xx1]
    dy_ = (ys - y) / (DY / 2.0)
    dx_ = (xs - x) / R
    inside = (np.abs(dy_) <= 1.0) & (np.abs(dx_) <= 1.0) & (np.abs(dy_) + 0.577 * np.abs(dx_) <= 1.15)
    return p[inside]

def feats(p):
    rr, gg, bb = p[:, 0], p[:, 1], p[:, 2]
    mx = p.max(axis=1); mn = p.min(axis=1)
    water = ((bb - rr > 25) & (bb > 110)).mean()
    tree = ((mx < 120) & (gg > rr)).mean()
    light = ((rr > 185) & (gg > 185) & (bb > 185)).mean()
    tan = ((rr > 165) & (gg > 140) & (bb < 130) & (rr - bb > 40)).mean()
    green = ((gg > rr + 15) & (gg > bb + 15) & (mx >= 120)).mean()
    grey = ((mx - mn < 40) & (mx >= 120) & (mx <= 190)).mean()
    return [water, tree, light, tan, green, grey]

data = {}
for path, cmax, rmax, yoff, r0 in (("_refs/map1.jpg", 20, 12, 96, 1),
                                  ("_refs/map2.jpg", 20, 23, 204, 13)):
    for c in range(1, cmax + 1):
        for r in range(r0, rmax + 1):
            p = interior(path, c, r, yoff, r0)
            if len(p) < 200:
                continue
            data["%02d%02d" % (c, r)] = feats(p)

keys = sorted(data)
X = np.array([data[k] for k in keys])
print("n hexes:", len(keys))
for k in keys:
    w, t, l, ta, g, gr = data[k]
    print("%s  water=%.2f tree=%.2f light=%.2f tan=%.2f green=%.2f grey=%.2f" % (k, w, t, l, ta, g, gr))
