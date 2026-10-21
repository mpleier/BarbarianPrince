"""Regenerate the hex-side river/road data using the *verified* grid.

The original _refs/detect_links.py used its own neighbour function whose
west-side entries were mirrored (odd columns got (c-1, r+1) instead of
(c-1, r-1), even columns got (c-1, r-1) instead of (c-1, r+1)), so it
sampled centre-to-centre segments that do not cross a real hex side.  That
is the source of the 39 "river sides" that are not geometric neighbours.

This version imports geometry.neighbours, which is symmetric and matches the
measured lattice (even columns shifted down by DY/2).
"""
import json
import math
import os
import sys

from PIL import Image
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, R, DX, DY, SCANS, centre, neighbours, hex_id

MAPS = [('map1.jpg', 1, 12), ('map2.jpg', 13, 23)]


def road_mask(path):
    a = np.array(Image.open(os.path.join('_refs', path)).convert('RGB')).astype(int)
    rr, gg, bb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (rr > 115) & (rr - gg > 22) & (rr - bb > 18) & (gg < 175) & (bb < 165)


def blue_mask(path):
    a = np.array(Image.open(os.path.join('_refs', path)).convert('RGB')).astype(int)
    rr, gg, bb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (bb > rr + 25) & (bb > 110)


def main():
    links = {}
    for name, r0, r1 in MAPS:
        rm = road_mask(name)
        bm = blue_mask(name)
        H, W = rm.shape
        for c in range(1, NC + 1):
            for r in range(r0, r1 + 1):
                p1 = centre(c, r, name)
                for d, hid in neighbours(c, r).items():
                    nc, nr = parse(hid)
                    key = tuple(sorted(((c, r), (nc, nr))))
                    if key in links:
                        continue
                    p2 = centre(nc, nr, name)
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
                    links[key] = (round(bh / max(tot, 1), 3), round(rh / max(tot, 1), 3))

    out = {'%02d%02d|%02d%02d' % (k[0][0], k[0][1], k[1][0], k[1][1]): v
           for k, v in links.items()}
    with open('_refs/road_links_fixed.json', 'w') as f:
        json.dump(out, f, indent=1)
    rivers = sorted(k for k, v in out.items() if v[0] > 0.35)
    roads = sorted(k for k, v in out.items() if v[1] > 0.35)
    print('adjacent pairs scanned:', len(out))
    print('river sides:', len(rivers))
    print('road sides:', len(roads))
    for k in rivers:
        print('  river', k, out[k])
    for k in roads:
        print('  road ', k, out[k])


def parse(hid):
    return int(hid[:2]), int(hid[2:])


if __name__ == '__main__':
    main()
