import math
from PIL import Image, ImageDraw
from map_model import R, NC, NR

SQ3 = math.sqrt(3.0)
DY = SQ3 * R
X0, Y0 = 377.0, 96.0
im = Image.open('map1.jpg').convert('RGB')
dr = ImageDraw.Draw(im)
for col in range(1, 8):
    for row in range(1, 8):
        i = col - 1
        cx = X0 + 1.5 * R * i
        cy = Y0 + DY * (row - 1) + (i % 2) * DY / 2.0
        pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
               for a in range(0, 360, 60)]
        dr.polygon(pts, outline=(255, 0, 0), width=3)
        dr.text((cx - 20, cy - 10), f'{col:02d}{row:02d}', fill=(255, 0, 0))
im.crop((200, 0, 1400, 1300)).save('gridcheck.jpg', quality=85)
print('saved')
