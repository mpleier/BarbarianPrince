import math
from PIL import Image, ImageDraw

SQ3 = math.sqrt(3.0)
R = 106.0
DX, DY = 1.5 * R, SQ3 * R
NC, NR = 20, 23
PAR = {'map1.jpg': (377.0, 96.0, 1), 'map2.jpg': (377.0, 199.0, 13)}


def render(path, out, scale=0.45):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    dr = ImageDraw.Draw(im)
    x0, y0, r0 = PAR[path]
    for col in range(1, NC + 1):
        for row in range(r0, NR + 1):
            i = col - 1
            cx = x0 + DX * i
            cy = y0 + DY * (row - r0) + (i % 2) * DY / 2.0
            if cx < -R or cx > W + R or cy < -R or cy > H + R:
                continue
            pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
                   for a in range(0, 360, 60)]
            dr.polygon(pts, outline=(255, 0, 0))
            dr.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(0, 0, 255))
            dr.text((cx - 12, cy - 10), f'{col:02d}{row:02d}', fill=(255, 255, 0))
    im = im.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    im.save(out)
    print(out, im.size)


render('map1.jpg', 'gridcheck_full1.png')
render('map2.jpg', 'gridcheck_full2.png')
