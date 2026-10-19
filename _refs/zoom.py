import math
import numpy as np
from PIL import Image
from build_map import center, R, NC, NR

CELL = 100
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
    for ri, row in enumerate(rows):
        for col in range(1, NC + 1):
            p = best_scan(col, row)
            W, H = SZ[p]
            cx, cy = center(col, row)
            x1, y1 = max(0, int(cx - R)), max(0, int(cy - R))
            x2, y2 = min(W, int(cx + R)), min(H, int(cy + R))
            s.paste(IM[p].crop((x1, y1, x2, y2)).resize((CELL, CELL)),
                    ((col - 1) * CELL, ri * CELL))
    s.save(out, quality=88)
    print(out, s.size)

sheet(list(range(1, 6)), 'z1a.jpg')
sheet(list(range(6, 11)), 'z1b.jpg')
sheet(list(range(11, 13)), 'z1c.jpg')
sheet(list(range(13, 18)), 'z2a.jpg')
sheet(list(range(18, 23)), 'z2b.jpg')
