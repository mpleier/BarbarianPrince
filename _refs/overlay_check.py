"""Overlay the classified terrain on the real scans so mismatches are obvious."""
import os
import sys
import json
import math
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, R, centre, hex_corners

COLORS = {
    'farmland': (223, 233, 176), 'countryside': (169, 209, 138), 'forest': (47, 125, 67),
    'mountains': (201, 201, 216), 'hills': (195, 169, 118), 'badlands': (176, 101, 95),
    'swamp': (127, 182, 168), 'desert': (242, 217, 140), 'unknown': (216, 216, 216),
}

hexes = json.load(open('_refs/hexes.json'))
terr = {h['id']: h['terrain'] for h in hexes}

for name, p in [('map1.jpg', {'x0': 377.0, 'y0': 96.0, 'first_row': 1, 'last_row': 12}),
                ('map2.jpg', {'x0': 377.0, 'y0': 199.0, 'first_row': 13, 'last_row': 23})]:
    im = Image.open('_refs/' + name).convert('RGB')
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for c in range(1, NC + 1):
        for r in range(p['first_row'], p['last_row'] + 1):
            hid = '%02d%02d' % (c, r)
            pts = hex_corners(c, r, name)
            d.polygon(pts, fill=COLORS.get(terr.get(hid, 'unknown'), (216, 216, 216)) + (110,))
            cx, cy = centre(c, r, name)
            d.text((cx - 14, cy - 6), hid, fill=(0, 0, 0, 255))
    out = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    out.thumbnail((1200, 1200))
    out.save('_refs/overlay_' + name.replace('.jpg', '.png'))
    print('wrote overlay_' + name.replace('.jpg', '.png'))
