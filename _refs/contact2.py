import json, math
import numpy as np
from PIL import Image, ImageDraw
from build_map import center, SCAN_FOR_ROW, R, NC, NR, classify, sample_hex

CELL = 62
COLORS = {
    'countryside': (150, 215, 120), 'farmland': (215, 185, 130),
    'forest': (40, 110, 55), 'mountains': (175, 175, 215),
    'badlands': (165, 110, 100), 'desert': (245, 225, 130),
    'swamp': (95, 175, 165), 'water': (60, 120, 200), 'unknown': (255, 0, 0),
}

IM = {p: Image.open(p).convert('RGB') for p in ('map1.jpg', 'map2.jpg')}
SZ = {p: IM[p].size for p in IM}

def best_scan(col, row):
    best, bs = -1, None
    for p in ('map1.jpg', 'map2.jpg'):
        W, H = SZ[p]
        x0, y0, r0, _ = {'map1.jpg': (377.0, 96.0, 1, 12), 'map2.jpg': (377.0, 199.0, 13, 23)}[p]
        i, j = col - 1, row - r0
        cx, cy = x0 + 1.5 * R * i, y0 + math.sqrt(3) * R * j + (i % 2) * math.sqrt(3) * R / 2
        area = max(0, min(H, cy + R) - max(0, cy - R)) * max(0, min(W, cx + R) - max(0, cx - R))
        if area > best:
            best, bs = area, p
    return bs

for scan in ('map1.jpg', 'map2.jpg'):
    rows = [r for r in range(1, NR + 1) if best_scan(1, r) == scan]
    sheet = Image.new('RGB', (NC * CELL, len(rows) * CELL), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    for ri, row in enumerate(rows):
        for col in range(1, NC + 1):
            p = best_scan(col, row)
            W, H = SZ[p]
            cx, cy = center(col, row)
            x1, y1 = int(cx - R), int(cy - R)
            x2, y2 = int(cx + R), int(cy + R)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(W, x2), min(H, y2)
            crop = IM[p].crop((x1, y1, x2, y2)).resize((CELL, CELL))
            sheet.paste(crop, ((col - 1) * CELL, ri * CELL))
            t, _ = classify(sample_hex(col, row))
            dr.rectangle(((col - 1) * CELL, ri * CELL, (col - 1) * CELL + 12, ri * CELL + 12),
                         fill=COLORS[t])
            dr.text(((col - 1) * CELL + 14, ri * CELL + 2), f'{col:02d}{row:02d}', fill=(0, 0, 0))
    sheet.save(f'sheet_{scan[4]}_{rows[0]}_{rows[-1]}.jpg', quality=92)
    print(scan, rows[0], rows[-1], len(rows))
