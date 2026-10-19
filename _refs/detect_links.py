"""Detect road connections between adjacent hexes.

Roads on the board are drawn as lines running between hex centres, so a road
"link" is detected by sampling the centre-to-centre segment of each adjacent
pair and measuring the fraction of road-mask pixels along it.
"""
from PIL import Image
import numpy as np
import math
import json

R = 105.7
DX = 1.5 * R
DY = math.sqrt(3) * R

MAPS = [("_refs/map1.jpg", 20, 12, 96, 1),
        ("_refs/map2.jpg", 20, 23, 204, 13)]


def centre(c, r, yoff, r0):
    return (380 + DX * (c - 1), yoff + DY * (r - r0) + (DY / 2 if c % 2 == 0 else 0))


def neighbours(c, r):
    if c % 2 == 1:
        return [(c, r - 1), (c, r + 1), (c + 1, r), (c + 1, r - 1),
                (c - 1, r), (c - 1, r + 1)]
    return [(c, r - 1), (c, r + 1), (c + 1, r), (c + 1, r + 1),
            (c - 1, r), (c - 1, r - 1)]


def road_mask(path):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    rr, gg, bb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (rr > 115) & (rr - gg > 22) & (rr - bb > 18) & (gg < 175) & (bb < 165)


def blue_mask(path):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    rr, gg, bb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (bb > rr + 25) & (bb > 110)


def main():
    links = {}
    for path, cmax, rmax, yoff, r0 in MAPS:
        rm = road_mask(path)
        bm = blue_mask(path)
        H, W = rm.shape
        for c in range(1, cmax + 1):
            for r in range(r0, rmax + 1):
                p1 = centre(c, r, yoff, r0)
                for nc, nr in neighbours(c, r):
                    if nc < 1 or nc > cmax or nr < r0 or nr > rmax:
                        continue
                    key = tuple(sorted(((c, r), (nc, nr))))
                    if key in links:
                        continue
                    p2 = centre(nc, nr, yoff, r0)
                    rh = bh = tot = 0
                    for t in np.linspace(0.30, 0.70, 41):
                        x = int(round(p1[0] + (p2[0] - p1[0]) * t))
                        y = int(round(p1[1] + (p2[1] - p1[1]) * t))
                        for dx in (-2, -1, 0, 1, 2):
                            for dy in (-2, -1, 0, 1, 2):
                                sx, sy = x + dx, y + dy
                                if 0 <= sx < W and 0 <= sy < H:
                                    tot += 1
                                    if rm[sy, sx]:
                                        rh += 1
                                    if bm[sy, sx]:
                                        bh += 1
                    links[key] = (round(bh / max(tot, 1), 3),
                                  round(rh / max(tot, 1), 3))
    out = {"%02d%02d|%02d%02d" % (k[0][0], k[0][1], k[1][0], k[1][1]): v
           for k, v in links.items()}
    with open("_refs/road_links.json", "w") as f:
        json.dump(out, f, indent=1)
    roads = sorted(k for k, v in out.items() if v[1] > 0.35)
    rivers = sorted(k for k, v in out.items() if v[0] > 0.35)
    print("road links:", len(roads))
    print("river links:", len(rivers))
    for k in roads:
        print("  road", k, out[k][1])



if __name__ == "__main__":
    main()
