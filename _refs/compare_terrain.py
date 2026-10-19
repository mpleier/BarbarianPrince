"""Compare a colour-based terrain classifier against the manual transcription."""
from PIL import Image
import numpy as np
import math
import json

R = 105.7
DX = 1.5 * R
DY = math.sqrt(3) * R

MANUAL = {
    1: "F M M M M C C M B B B F C S F B M M M M".split(),
    2: "C F F C C C C B C B B F S S S C B M M C".split(),
    3: "M F F M M C M F F F S F C C F M M C M B".split(),
    4: "C B M M M M C F F B C B F F F F C C B C".split(),
    5: "B B C M F B M F C F M M C F C F M M C B".split(),
    6: "D D C M B B F F C C M B B B M M M C C M".split(),
    7: "B D B D C F C C C C M M D B D D M M M B".split(),
    8: "C B C D F C C F F C B B D D D D M M M B".split(),
    9: "C C F F S C F F C C B B D D D D B M B B".split(),
    10: "C C F C C F S F C F C B D D D D C M C B".split(),
    11: "F C C S S F S F C B M B D B B C M C B M".split(),
    12: "F S C C S C S F C C B M B B B C B B C M".split(),
    13: "C S S C F C S F F C B M M F C B B B C M".split(),
    14: "S S F C F C C F S C M M C C C C C C C C".split(),
    15: "S S F C F C F F S C C B C F F C B F C F".split(),
    16: "F F C C F F F F F S C C F F F C F S F S".split(),
    17: "F F F C C C C F C S F C F F F S F F F F".split(),
    18: "F F C F F F C C F F S F C F F C B C C C".split(),
    19: "C F F F F F F F C B S F C F F C B C C C".split(),
    20: "C F C F C C C C C B F F C F F C F C F F".split(),
    21: "C F C F C C F C C M F C C S F S F F F F".split(),
    22: "C F F F F C C C B M C C C S S S F F F F".split(),
    23: "F F F F C C F C B M M F S S S C C F F F".split(),
}

def interior(path, c, r, yoff, r0):
    a = np.array(Image.open(path).convert("RGB")).astype(float)
    H, W, _ = a.shape
    x = 380 + DX * (c - 1)
    y = yoff + DY * (r - r0) + (DY / 2 if c % 2 == 0 else 0)
    rad = 0.62 * R
    yy0, yy1 = max(int(y - rad), 0), min(int(y + rad) + 1, H)
    xx0, xx1 = max(int(x - rad), 0), min(int(x + rad) + 1, W)
    p = a[yy0:yy1, xx0:xx1]
    ys, xs = np.mgrid[yy0:yy1, xx0:xx1]
    inside = (np.abs(ys - y) / (DY / 2.0) + 0.577 * np.abs(xs - x) / R) <= 1.1
    return p[inside]

def classify(p):
    rr, gg, bb = p[:, 0], p[:, 1], p[:, 2]
    mx = p.max(axis=1)
    water = float(((bb - rr > 25) & (bb > 110)).mean())
    tree = float(((mx < 120) & (gg > rr)).mean())
    light = float(((rr > 185) & (gg > 185) & (bb > 185)).mean())
    tan = float(((rr > 165) & (gg > 140) & (bb < 130) & (rr - bb > 40)).mean())
    green = float(((gg > rr + 15) & (gg > bb + 15) & (mx >= 120)).mean())
    grey = float(((mx - p.min(axis=1) < 40) & (mx >= 120) & (mx <= 190)).mean())
    if water > 0.30:
        return "S"
    if tree > 0.30:
        return "F"
    if light > 0.25:
        return "M"
    if grey > 0.22 and green < 0.30:
        return "B"
    if tan > 0.35 and green < 0.30:
        return "D"
    if green > 0.45:
        return "C"
    return "?"

data = {}
for r in range(1, 24):
    for c in range(1, 21):
        path, yoff, r0 = ("_refs/map1.jpg", 96, 1) if r <= 12 else ("_refs/map2.jpg", 204, 13)
        p = interior(path, c, r, yoff, r0)
        if len(p) < 200:
            continue
        data[(c, r)] = classify(p)

diff = []
for r in range(1, 24):
    for c in range(1, 21):
        m = MANUAL[r][c - 1]
        a = data.get((c, r), "?")
        if m != a:
            diff.append((c, r, m, a))
print("manual vs auto disagreements: %d / 460" % len(diff))
for c, r, m, a in diff:
    print("  %02d%02d manual=%s auto=%s" % (c, r, m, a))
