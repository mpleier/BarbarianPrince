"""Identify which hexes contain a drawn road (roads cut across hex interiors)."""
from PIL import Image
import numpy as np
import math
import json

R = 105.7
DX = 1.5 * R
DY = math.sqrt(3) * R

def road_hexes(path, cmax, rmax, yoff, r0):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    rr, gg, bb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = (rr > 120) & (rr - gg > 25) & (rr - bb > 20) & (gg < 170) & (bb < 160)
    H, W = mask.shape
    out = {}
    for c in range(1, cmax + 1):
        for r in range(r0, rmax + 1):
            x = 380 + DX * (c - 1)
            y = yoff + DY * (r - r0) + (DY / 2 if c % 2 == 0 else 0)
            rad = 0.75 * R
            yy0, yy1 = max(int(y - rad), 0), min(int(y + rad) + 1, H)
            xx0, xx1 = max(int(x - rad), 0), min(int(x + rad) + 1, W)
            sub = mask[yy0:yy1, xx0:xx1]
            ys, xs = np.mgrid[yy0:yy1, xx0:xx1]
            inside = (np.abs(ys - y) / (DY / 2) + 0.577 * np.abs(xs - x) / R) <= 1.1
            tot = inside.sum()
            if tot:
                out["%02d%02d" % (c, r)] = round(float(sub[inside].sum()) / tot, 3)
    return out

res = road_hexes("_refs/map1.jpg", 20, 12, 96, 1)
res.update(road_hexes("_refs/map2.jpg", 20, 23, 204, 13))
with open("_refs/roadhexes.json", "w") as f:
    json.dump(res, f, indent=1)
for r in range(1, 24):
    print("row %2d: " % r + " ".join("%s" % ("R" if res.get("%02d%02d" % (c, r), 0) > 0.12 else "." for c in range(1, 21)))
        + "  " + " ".join("%.2f" % res.get("%02d%02d" % (c, r), 0) for c in range(1, 21)))
