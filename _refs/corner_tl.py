"""Overlay the model grid on the top-left corner of map1 to pin down x0."""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import R, DX, DY, SCANS

im = Image.open('_refs/map1.jpg').convert('RGB')
d = ImageDraw.Draw(im)
x0, y0 = SCANS['map1.jpg']['x0'], SCANS['map1.jpg']['y0']
for c in range(1, 5):
    for r in range(1, 4):
        cx = x0 + DX * (c - 1)
        cy = y0 + DY * (r - 1) + (c - 1) % 2 * DY / 2.0
        pts = [(cx + R * math.cos(math.radians(a)),
                cy + R * math.sin(math.radians(a))) for a in range(0, 360, 60)]
        d.line(pts + pts[0:1], fill=(255, 0, 0), width=2)
        d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(0, 0, 255))
im.crop((0, 0, 900, 600)).save('_refs/corner_tl_map1.png')
print('wrote _refs/corner_tl_map1.png')
