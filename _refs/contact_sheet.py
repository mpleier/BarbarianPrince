"""Build a contact sheet of every map hex interior from map1.jpg for visual
verification of the fitted hex lattice and terrain classification."""
import math
import numpy as np
from PIL import Image, ImageDraw

SQ3 = math.sqrt(3.0)
NC, NR = 23, 20
R = 105
X0, Y0 = 386, 103
DX, DY = 1.5 * R, SQ3 * R

im = Image.open('map1.jpg').convert('RGB')
A = np.asarray(im, dtype=np.float32)
H, W = A.shape[:2]

def center(c, r):
    return X0 + c * DX, Y0 + r * DY + (c % 2) * DY / 2.0

CELL = 62
sheet = Image.new('RGB', (NC * CELL, NR * CELL), (255, 255, 255))
dr = ImageDraw.Draw(sheet)

for c in range(NC):
    for r in range(NR):
        cx, cy = center(c, r)
        x1, y1 = int(cx - R), int(cy - R)
        x2, y2 = int(cx + R), int(cy + R)
        if x1 < 0 or y1 < 0 or x2 > W or y2 > H:
            continue
        crop = im.crop((x1, y1, x2, y2)).resize((CELL, CELL))
        sheet.paste(crop, (c * CELL, r * CELL))
        dr.text((c * CELL + 2, r * CELL + 2), f'{r+1:02d}{c+1:02d}', fill=(0, 0, 0))

sheet.save('contact_sheet.png')
print('saved contact_sheet.png', sheet.size)
