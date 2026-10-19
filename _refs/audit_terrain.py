"""Audit terrain: compare each hex's mean interior colour with its class mean."""
import os
import sys
import json
import math
import numpy as np
from PIL import Image
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, NR, R, SCANS, centre, hex_id

hexes = json.load(open('_refs/hexes.json'))
IMG = {p: np.asarray(Image.open('_refs/' + p).convert('RGB'), dtype=np.float32) for p in SCANS}

def interior(scan, c, r, rad=0.62):
    A = IMG[scan]
    H, W = A.shape[:2]
    cx, cy = centre(c, r, scan)
    x1, x2 = int(cx - rad * R), int(cx + rad * R)
    y1, y2 = int(cy - rad * R), int(cy + rad * R)
    x1, x2 = max(0, x1), min(W, x2)
    y1, y2 = max(0, y1), min(H, y2)
    if x2 <= x1 or y2 <= y1:
        return np.zeros((0, 3), dtype=np.float32)
    sub = A[y1:y2, x1:x2]
    ys, xs = np.mgrid[y1:y2, x1:x2]
    dx = np.abs(xs - cx) / R
    dy = np.abs(ys - cy) / (R * math.sqrt(3) / 2)
    m = (dx <= 1) & (dy <= 1) & (dy + 0.577 * dx <= 1.15)
    px = sub[m]
    px = px[px.min(axis=1) < 200]      # drop white grid lines / label text
    return px

means = {}
for h in hexes:
    c, r = h['col'], h['row']
    scan = 'map1.jpg' if r <= 12 else 'map2.jpg'
    px = interior(scan, c, r)
    means[h['id']] = px.mean(axis=0) if len(px) else np.zeros(3)

groups = defaultdict(list)
for h in hexes:
    groups[h['terrain']].append(means[h['id']])

print('terrain  n   mean RGB')
for t, arr in sorted(groups.items()):
    a = np.array(arr)
    print('%-11s %3d  %6.1f %6.1f %6.1f' % (t, len(a), a[:, 0].mean(), a[:, 1].mean(), a[:, 2].mean()))

# flag hexes whose mean colour is far from their class mean
print('\nOUTLIERS (distance from class mean > 40):')
n = 0
for h in hexes:
    a = np.array(groups[h['terrain']])
    d = np.linalg.norm(means[h['id']] - a.mean(axis=0))
    if d > 40:
        n += 1
        print('  %s %-11s mean=%s dist=%.1f' % (h['id'], h['terrain'],
              tuple(round(v, 1) for v in means[h['id']]), d))
print('total outliers:', n)
