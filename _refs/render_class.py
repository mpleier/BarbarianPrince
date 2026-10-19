import json, math
from PIL import Image, ImageDraw

SQ3 = math.sqrt(3.0)
R = 26.0
NC, NR = 20, 23
DX, DY = 1.5 * R, SQ3 * R

COLORS = {
    'countryside': (150, 215, 120),
    'farmland': (215, 185, 130),
    'forest': (40, 110, 55),
    'mountains': (175, 175, 215),
    'badlands': (165, 110, 100),
    'desert': (245, 225, 130),
    'swamp': (95, 175, 165),
    'water': (60, 120, 200),
    'unknown': (255, 0, 0),
}

hexes = json.load(open('hexes_raw.json'))
W = int(NC * DX + 2 * R) + 20
H = int(NR * DY + DY / 2) + 20
img = Image.new('RGB', (W, H), (250, 250, 250))
dr = ImageDraw.Draw(img)

def cxy(col, row):
    i, j = col - 1, row - 1
    return 10 + DX * i, 10 + DY * j + (i % 2) * DY / 2.0

for h in hexes:
    cx, cy = cxy(h['col'], h['row'])
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
           for a in range(0, 360, 60)]
    dr.polygon(pts, fill=COLORS[h['terrain']])
    dr.text((cx - 8, cy - 6), h['id'], fill=(0, 0, 0))
    for s in range(6):
        a = math.radians(30 + 60 * s)
        dr.line([(cx + R * math.cos(a), cy + R * math.sin(a)),
                 (cx + 0.55 * R * math.cos(a), cy + 0.55 * R * math.sin(a))],
                fill=(0, 0, 0))

img.save('classified.png')
print(img.size)
