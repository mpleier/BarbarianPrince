import json, math
import numpy as np
from PIL import Image, ImageDraw
from build_map import center, R, NC, NR, classify, sample_hex

CELL = 50
COLORS = {
    'countryside': (150, 215, 120), 'farmland': (215, 185, 130),
    'forest': (40, 110, 55), 'mountains': (175, 175, 215),
    'badlands': (165, 110, 100), 'desert': (245, 225, 130),
    'swamp': (95, 175, 165), 'water': (60, 120, 200), 'unknown': (255, 0, 0),
}
IM = {p: Image.open(p).convert('RGB') for p in ('map1.jpg', 'map2.jpg')}
SZ = {p: IM[p].size for p in IM}
PAR = {'map1.jpg': (377.0, 96.0, 1), 'map2.jpg': (377.0, 199.0, 13)}

def best_scan(col, row):
    best, bs = -1, None
    for p, (x0, y0, r0) in PAR.items():
        W, H = SZ[p]
        i = col - 1
        cx = x0 + 1.5 * R * i
        cy = y0 + math.sqrt(3) * R * (row - r0) + (i % 2) * math.sqrt(3) * R / 2
        area = max(0, min(H, cy + R) - max(0, cy - R)) * max(0, min(W, cx + R) - max(0, cx - R))
        if area > best:
            best, bs = area, p
    return bs

def sheet(rows, out):
    s = Image.new('RGB', (NC * CELL, len(rows) * CELL), (255, 255, 255))
    dr = ImageDraw.Draw(s)
    for ri, row in enumerate(rows):
        for col in range(1, NC + 1):
            p = best_scan(col, row)
            W, H = SZ[p]
            cx, cy = center(col, row)
            x1, y1 = max(0, int(cx - R)), max(0, int(cy - R))
            x2, y2 = min(W, int(cx + R)), min(H, int(cy + R))
            crop = IM[p].crop((x1, y1, x2, y2)).resize((CELL, CELL))
            s.paste(crop, ((col - 1) * CELL, ri * CELL))
            t, _ = classify(sample_hex(col, row))
            dr.rectangle(((col - 1) * CELL, ri * CELL, (col - 1) * CELL + 10, ri * CELL + 10),
                         fill=COLORS[t])
            dr.text(((col - 1) * CELL + 12, ri * CELL + 1), f'{col:02d}{row:02d}', fill=(0, 0, 0))
    s.save(out, quality=90)
    print(out, s.size)

sheet(list(range(1, 7)), 's1a.jpg')
sheet(list(range(7, 13)), 's1b.jpg')
sheet(list(range(13, 19)), 's2a.jpg')
sheet(list(range(19, 24)), 's2b.jpg')
