"""Fit the hex lattice to the two board scans, classify every hex's terrain,
and detect river/road crossings on hex sides.

Board geometry (verified against the scans):
  * flat-top hexes, 20 columns x 23 rows = 460 hexes
  * hex id = CCRR  (column 01-20, row 01-23)
  * map1.jpg holds rows 01-12, map2.jpg holds rows 13-23
"""
import json
import math
import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)
R = 106.0
NC, NR = 20, 23
DX, DY = 1.5 * R, SQ3 * R

SCANS = {
    'map1.jpg': (377.0, 96.0, 1, 12),    # x0, y0, first row, last row
    'map2.jpg': (377.0, 199.0, 13, 23),
}

def center(col, row):
    """col,row are 1-based. Returns (x, y) in the scan that holds this row."""
    scan = SCAN_FOR_ROW[row]
    x0, y0, r0, r1 = SCANS[scan]
    i, j = col - 1, row - r0
    return x0 + DX * i, y0 + DY * j + (i % 2) * DY / 2.0

SCAN_FOR_ROW = {r: ('map1.jpg' if r <= 12 else 'map2.jpg') for r in range(1, NR + 1)}

# side index -> angle of the side midpoint (degrees, image coords, y down)
SIDE_ANGLE = [30, 90, 150, 210, 270, 330]
SIDE_NAME = ['SE', 'S', 'SW', 'NW', 'N', 'NE']

def neighbour(col, row, side):
    """Return (ncol, nrow) across `side`, or None if off-board."""
    i, j = col - 1, row - 1
    if side == 1:   # S
        nj = j + 1
        ni = i
    elif side == 4: # N
        nj = j - 1
        ni = i
    elif side == 0: # SE
        ni = i + 1
        nj = j if i % 2 == 0 else j + 1
    elif side == 5: # NE
        ni = i + 1
        nj = j if i % 2 == 0 else j - 1
    elif side == 2: # SW
        ni = i - 1
        nj = j if i % 2 == 0 else j + 1
    else:           # NW
        ni = i - 1
        nj = j if i % 2 == 0 else j - 1
    if 1 <= ni + 1 <= NC and 1 <= nj + 1 <= NR:
        return ni + 1, nj + 1
    return None

IMG = {p: np.asarray(Image.open(p).convert('RGB'), dtype=np.int16) for p in SCANS}

def sample_hex(col, row, rad=0.72):
    scan = SCAN_FOR_ROW[row]
    A = IMG[scan]
    H, W = A.shape[:2]
    cx, cy = center(col, row)
    x1, x2 = int(cx - rad * R), int(cx + rad * R)
    y1, y2 = int(cy - rad * R), int(cy + rad * R)
    x1, x2 = max(0, x1), min(W, x2)
    y1, y2 = max(0, y1), min(H, y2)
    sub = A[y1:y2, x1:x2].astype(np.float32)
    if sub.size == 0:
        return np.zeros((0, 3))
    ys, xs = np.mgrid[y1:y2, x1:x2]
    d = np.hypot(xs - cx, ys - cy)
    m = d <= rad * R
    px = sub[m]
    # drop the white grid lines / white label text
    keep = px.min(axis=1) < 195
    return px[keep]

def classify(px):
    if len(px) < 50:
        return 'unknown', {}
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    lum = (r + g + b) / 3.0
    water = (b > r + 20) & (b > g + 8) & (b > 90)
    tree = (g > r + 5) & (g >= b) & (lum < 145)
    grass = (g > r + 5) & (g > b) & (lum >= 145)
    yellow = (r > g + 15) & (g > b + 10) & (lum > 175)
    brown = (r > g + 15) & (r > b + 20) & (lum <= 175)
    purple = (b > g + 10) & (r > g + 5)
    grey = (abs(r - g) < 22) & (abs(g - b) < 22) & (lum < 200)
    f = {
        'water': float(water.mean()),
        'tree': float(tree.mean()),
        'grass': float(grass.mean()),
        'yellow': float(yellow.mean()),
        'brown': float(brown.mean()),
        'purple': float(purple.mean()),
        'grey': float(grey.mean()),
    }
    if f['water'] > 0.30:
        t = 'swamp' if f['tree'] + f['grass'] > 0.25 else 'water'
    elif f['tree'] > 0.30:
        t = 'forest'
    elif f['purple'] > 0.22 or f['grey'] > 0.30:
        t = 'mountains'
    elif f['brown'] > 0.30:
        t = 'badlands'
    elif f['yellow'] > 0.30:
        t = 'desert'
    elif f['grass'] + f['tree'] > 0.45:
        t = 'countryside'
    elif f['brown'] + f['yellow'] > 0.20:
        t = 'farmland'
    else:
        t = 'countryside'
    return t, f

def side_feature(col, row, side, kind):
    """kind = 'water' or 'road': does the feature cross this hex side?"""
    scan = SCAN_FOR_ROW[row]
    A = IMG[scan]
    H, W = A.shape[:2]
    cx, cy = center(col, row)
    ang = math.radians(SIDE_ANGLE[side])
    r, g, b = A.astype(np.float32), None, None
    hits = 0
    tot = 0
    for t in np.linspace(-0.42, 0.42, 15):
        # walk across the boundary: from just inside to just outside
        for off in (0.86, 0.95, 1.05, 1.15):
            px = int(round(cx + (off * R) * math.cos(ang) + t * R * math.sin(ang) * 0.9))
            py = int(round(cy + (off * R) * math.sin(ang) - t * R * math.cos(ang) * 0.9))
            if px < 0 or py < 0 or px >= W or py >= H:
                continue
            pr, pg, pb = A[py, px]
            tot += 1
            if kind == 'water':
                if pb > pr + 20 and pb > pg + 8 and pb > 90:
                    hits += 1
            else:
                if pr > pg + 25 and pr > pb + 25 and pr > 110:
                    hits += 1
    return hits / tot if tot else 0.0

def build():
    hexes = []
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            px = sample_hex(col, row)
            t, f = classify(px)
            hid = f'{col:02d}{row:02d}'
            nb = {}
            for s in range(6):
                n = neighbour(col, row, s)
                if n:
                    nb[SIDE_NAME[s]] = f'{n[0]:02d}{n[1]:02d}'
            hexes.append({'id': hid, 'col': col, 'row': row, 'terrain': t,
                          'frac': {k: round(v, 3) for k, v in f.items()},
                          'neighbors': nb})
    return hexes

if __name__ == '__main__':
    hexes = build()
    json.dump(hexes, open('hexes_raw.json', 'w'), indent=1)
    from collections import Counter
    print(Counter(h['terrain'] for h in hexes))
    print(len(hexes))
