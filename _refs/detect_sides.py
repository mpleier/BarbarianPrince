"""Detect river and road hex-sides from the map scans."""
from PIL import Image
import numpy as np
import math
import json

R = 105.7
DX = 1.5 * R
DY = math.sqrt(3) * R

def center(c, r, yoff, r0):
    return (380 + DX * (c - 1), yoff + DY * (r - r0) + (DY / 2 if c % 2 == 0 else 0))

def neighbours(c, r):
    if c % 2 == 1:  # odd column: even columns sit half a row lower
        return [(c, r - 1), (c, r + 1), (c + 1, r), (c + 1, r - 1),
                (c - 1, r), (c - 1, r + 1)]
    return [(c, r - 1), (c, r + 1), (c + 1, r), (c + 1, r + 1),
            (c - 1, r), (c - 1, r - 1)]

def edge_points(p1, p2):
    """The two shared vertices of the hex-side between adjacent hexes p1,p2."""
    x1, y1 = p1
    x2, y2 = p2
    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    # direction from p1 to p2
    vx, vy = x2 - x1, y2 - y1
    n = math.hypot(vx, vy)
    vx, vy = vx / n, vy / n
    # the shared edge is perpendicular to the line of centres, half a side long
    # side length = R; edge endpoints are mx +/- R/2 along the perpendicular
    px, py = -vy, vx
    return (mx + px * R / 2, my + py * R / 2), (mx - px * R / 2, my - py * R / 2)

def scan(path, cmax, rmax, yoff, r0):
    a = np.array(Image.open(path).convert("RGB")).astype(float)
    H, W, _ = a.shape
    res = {}
    for c in range(1, cmax + 1):
        for r in range(r0, rmax + 1):
            p1 = center(c, r, yoff, r0)
            for nc, nr in neighbours(c, r):
                if nc < 1 or nc > cmax or nr < r0 or nr > rmax:
                    continue
                key = tuple(sorted(((c, r), (nc, nr))))
                if key in res:
                    continue
                p2 = center(nc, nr, yoff, r0)
                e1, e2 = edge_points(p1, p2)
                blue = road = 0.0
                tot = 0
                for t in np.linspace(0.1, 0.9, 25):
                    bx = e1[0] + (e2[0] - e1[0]) * t
                    by = e1[1] + (e2[1] - e1[1]) * t
                    for off in (-14, 0, 14):
                        ang = math.atan2(e2[1] - e1[1], e2[0] - e1[0]) + math.pi / 2
                        sx = int(bx + off * math.cos(ang))
                        sy = int(by + off * math.sin(ang))
                        if 0 <= sx < W and 0 <= sy < H:
                            rr, gg, bb = a[sy, sx]
                            tot += 1
                            if bb > rr + 25 and bb > 110:
                                blue += 1
                            if rr > 120 and gg < 110 and bb < 100 and rr - gg > 30:
                                road += 1
                res[key] = (round(blue / max(tot, 1), 3), round(road / max(tot, 1), 3))
    return res

res = scan("_refs/map1.jpg", 20, 12, 96, 1)
res.update(scan("_refs/map2.jpg", 20, 23, 204, 13))
with open("_refs/hexsides.json", "w") as f:
    json.dump({"%d,%d|%d,%d" % (k[0][0], k[0][1], k[1][0], k[1][1]): v
               for k, v in res.items()}, f, indent=1)

print("RIVER SIDES (blue fraction > 0.35):")
for k, v in sorted(res.items()):
    if v[0] > 0.35:
        print(" ", k, v[0])
print("\nROAD SIDES (road fraction > 0.3):")
for k, v in sorted(res.items()):
    if v[1] > 0.3:
        print(" ", k, v[1])
