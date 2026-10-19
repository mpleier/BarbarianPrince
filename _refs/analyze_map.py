"""Hex-lattice sampling helper: dump per-hex colour statistics for validation."""
from PIL import Image
import numpy as np
import math
import json

R = 105.7
DX = 1.5 * R
DY = math.sqrt(3) * R


def hex_center(c, r, yoff, r0):
    x = 380 + DX * (c - 1)
    y = yoff + DY * (r - r0) + (DY / 2 if c % 2 == 0 else 0)
    return x, y


def stats(path, cmax, rmax, yoff, r0):
    a = np.array(Image.open(path).convert("RGB")).astype(float)
    H, W, _ = a.shape
    out = {}
    for c in range(1, cmax + 1):
        for r in range(r0, rmax + 1):
            x, y = hex_center(c, r, yoff, r0)
            rad = 0.5 * R
            yy0, yy1 = int(y - rad), int(y + rad) + 1
            xx0, xx1 = int(x - rad), int(x + rad) + 1
            if yy0 < 0 or yy1 > H or xx0 < 0 or xx1 > W:
                continue
            p = a[yy0:yy1, xx0:xx1]
            rr, gg, bb = p[:, :, 0], p[:, :, 1], p[:, :, 2]
            dark = float((p.max(axis=2) < 100).mean())
            white = float(((rr > 190) & (gg > 190) & (bb > 190)).mean())
            blue = float((bb > rr + 25).mean())
            green = float(((gg > rr + 10) & (gg > bb + 10)).mean())
            yellow = float(((rr > 150) & (gg > 120) & (bb < 110)).mean())
            out["%02d%02d" % (c, r)] = [round(dark, 3), round(white, 3),
                                        round(blue, 3), round(green, 3),
                                        round(yellow, 3)]
    return out


s = stats("_refs/map1.jpg", 20, 12, 96, 1)
s.update(stats("_refs/map2.jpg", 20, 23, 204, 13))
with open("_refs/hexstats.json", "w") as f:
    json.dump(s, f, indent=1)

def classify(v):
    dark, white, blue, green, yellow = v
    if blue > 0.25:
        return "oasis/swamp-water"
    if dark > 0.28:
        return "forest"
    if white > 0.22:
        return "mountains"
    if yellow > 0.35 and green < 0.25:
        return "desert/badlands"
    if green > 0.55:
        return "countryside/farmland"
    return "?"

for k in sorted(s):
    print(k, classify(s[k]), s[k])
