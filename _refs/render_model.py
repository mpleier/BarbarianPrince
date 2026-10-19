import json
import math
from PIL import Image, ImageDraw
from map_model import R, NC, NR, centre, SIDE_ANGLE

hexes = json.load(open('hexes.json'))
COLORS = {
    'countryside': (150, 215, 120), 'farmland': (220, 190, 130),
    'forest': (40, 110, 55), 'mountains': (175, 175, 215),
    'badlands': (165, 110, 100), 'desert': (245, 225, 130),
    'swamp': (95, 175, 165), 'water': (60, 120, 200), 'unknown': (255, 0, 0),
}
SCALE = 0.42
SQ3 = math.sqrt(3.0)
DY = SQ3 * R
X0, Y0 = 377.0, 96.0
W = int((X0 + 1.5 * R * (NC - 1) + R + 40) * SCALE)
H = int((Y0 + DY * (NR - 1) + R + 40) * SCALE)
img = Image.new('RGB', (W, H), (255, 255, 255))
dr = ImageDraw.Draw(img)

for h in hexes:
    i = h['col'] - 1
    cx = X0 + 1.5 * R * i
    cy = Y0 + DY * (h['row'] - 1) + (i % 2) * DY / 2.0
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
           for a in range(0, 360, 60)]
    pts = [(x * SCALE, y * SCALE) for x, y in pts]
    dr.polygon(pts, fill=COLORS[h['terrain']])
    dr.text((cx * SCALE - 8, cy * SCALE - 6), h['id'], fill=(30, 30, 30))

img.save('model_map.png')
img.resize((W // 2, H // 2)).save('model_map_small.png')
print(img.size)
