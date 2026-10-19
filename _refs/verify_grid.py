"""Overlay the computed hex grid on each scan to verify alignment."""
import os
import sys
import math
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, NR, R, SCANS, centre, hex_corners

for name, p in SCANS.items():
    im = Image.open(os.path.join('_refs', name)).convert('RGB')
    d = ImageDraw.Draw(im)
    cmax = p['last_row']
    for c in range(1, NC + 1):
        for r in range(p['first_row'], cmax + 1):
            pts = hex_corners(c, r, name)
            d.polygon([(x, y) for x, y in pts], outline=(255, 0, 0), width=2)
            cx, cy = centre(c, r, name)
            d.text((cx - 12, cy - 6), '%02d%02d' % (c, r), fill=(0, 0, 255))
    im.save(os.path.join('_refs', 'gridcheck_' + name.replace('.jpg', '.png')))
    print('wrote gridcheck_' + name.replace('.jpg', '.png'), im.size)
