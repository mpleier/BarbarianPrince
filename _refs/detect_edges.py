"""Detect river/road hex sides by sampling exactly along the shared edge.

The earlier centre-to-centre sampling in _refs/detect_links.py also caught
blue pixels belonging to a river that runs along a *neighbouring* edge, which
is why so many false "river sides" appeared.  Sampling the shared edge itself
is unambiguous.
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, R, DX, DY, SCANS, centre, neighbours, hex_id, board_xy, board_corners

MAPS = [('map1.jpg', 1, 12), ('map2.jpg', 13, 23)]


def masks(path):
    a = np.array(Image.open(os.path.join('_refs', path)).convert('RGB')).astype(int)
    rr, gg, bb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    blue = (bb > rr + 20) & (bb > 100) & (bb > gg + 5)
    road = (rr > 115) & (rr - gg > 22) & (rr - bb > 18) & (gg < 175) & (bb < 165)
    return blue, road


def shared_edge(p1, p2):
    mx, my = (p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0
    vx, vy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(vx, vy)
    px, py = -vy / n, vx / n
    return (mx + px * R / 2, my + py * R / 2), (mx - px * R / 2, my - py * R / 2)


def main():
    sides = {}
    for name, r0, r1 in MAPS:
        blue, road = masks(name)
        H, W = blue.shape
        for c in range(1, NC + 1):
            for r in range(r0, r1 + 1):
                p1 = centre(c, r, name)
                for d, hid in neighbours(c, r).items():
                    nc, nr = int(hid[:2]), int(hid[2:])
                    key = tuple(sorted(((c, r), (nc, nr))))
                    if key in sides:
                        continue
                    p2 = centre(nc, nr, name)
                    e1, e2 = shared_edge(p1, p2)
                    bt = rt = tot = 0
                    for t in np.linspace(0.05, 0.95, 40):
                        bx = e1[0] + (e2[0] - e1[0]) * t
                        by = e1[1] + (e2[1] - e1[1]) * t
                        for off in (-6, 0, 6):
                            ang = math.atan2(e2[1] - e1[1], e2[0] - e1[0]) + math.pi / 2
                            sx = int(round(bx + off * math.cos(ang)))
                            sy = int(round(by + off * math.sin(ang)))
                            if 0 <= sx < W and 0 <= sy < H:
                                tot += 1
                                if blue[sy, sx]:
                                    bt += 1
                                if road[sy, sx]:
                                    rt += 1
                    sides[key] = (round(bt / max(tot, 1), 3), round(rt / max(tot, 1), 3))

    out = {'%02d%02d|%02d%02d' % (k[0][0], k[0][1], k[1][0], k[1][1]): v
           for k, v in sides.items()}
    with open('_refs/hexsides_edge.json', 'w') as f:
        json.dump(out, f, indent=1)

    riv = sorted(k for k, v in out.items() if v[0] > 0.5)
    rd = sorted(k for k, v in out.items() if v[1] > 0.5)
    print('edges scanned:', len(out))
    print('river sides:', len(riv))
    for k in riv:
        print('  ', k, out[k])
    print('road sides:', len(rd))
    for k in rd:
        print('  ', k, out[k])

    # render an overlay for visual verification, one image per scan
    for name, r0, r1 in MAPS:
        im = Image.open(os.path.join('_refs', name)).convert('RGB')
        d = ImageDraw.Draw(im)
        for k in riv:
            a, b = k.split('|')
            ac, ar = int(a[:2]), int(a[2:])
            bc, br = int(b[:2]), int(b[2:])
            if not (r0 <= ar <= r1 and r0 <= br <= r1):
                continue
            e1, e2 = shared_edge(centre(ac, ar, name), centre(bc, br, name))
            d.line([e1, e2], fill=(0, 0, 255), width=6)
        for k in rd:
            a, b = k.split('|')
            ac, ar = int(a[:2]), int(a[2:])
            bc, br = int(b[:2]), int(b[2:])
            if not (r0 <= ar <= r1 and r0 <= br <= r1):
                continue
            e1, e2 = shared_edge(centre(ac, ar, name), centre(bc, br, name))
            d.line([e1, e2], fill=(255, 0, 0), width=4)
        im.save('_refs/sides_overlay_' + name.replace('.jpg', '.png'))
        print('wrote _refs/sides_overlay_' + name.replace('.jpg', '.png'), im.size)


if __name__ == '__main__':
    main()
