"""Least-squares fit of the column lattice from full-length printed flat edges.

On every horizontal grid line a printed flat hex edge is R px long and is
centred on the column axis.  Collect all runs at least ~R px wide and fit
centre = x0 + DX * (col - 1).
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, R, DX, DY, SCANS


def line_ys(A, band):
    sub = A[:, band[0]:band[1]].min(axis=2) > 200
    frac = sub.mean(axis=1)
    ys, i, n = [], 0, len(frac)
    while i < n:
        if frac[i] > 0.45:
            j = i
            while j + 1 < n and frac[j + 1] > 0.45:
                j += 1
            ys.append((i + j) / 2.0)
            i = j + 1
        else:
            i += 1
    return ys


def flat_edge_centres(A, y):
    row = A[int(round(y)) - 2:int(round(y)) + 3].min(axis=2).mean(axis=0)
    white = row > 200
    out, start = [], None
    for x, w in enumerate(white):
        if w and start is None:
            start = x
        elif not w and start is not None:
            if x - start >= 95:
                out.append((start + x - 1) / 2.0)
            start = None
    if start is not None and len(white) - start >= 95:
        out.append((start + len(white) - 1) / 2.0)
    return out


for name, first_row in (('map1.jpg', 1), ('map2.jpg', 13)):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    p = SCANS[name]
    ys = line_ys(A, (324, 431))
    pts = []
    for y in ys:
        k = (y - p['y0']) / DY + 0.5
        if abs(k - round(k)) > 0.05:
            continue
        for cx in flat_edge_centres(A, y):
            col = round((cx - p['x0']) / DX) + 1
            if 1 <= col <= NC and col % 2 == 1:
                pts.append((col - 1, cx))
    if not pts:
        print(name, 'no edges found')
        continue
    idx = np.array([i for i, _ in pts], dtype=float)
    val = np.array([v for _, v in pts])
    slope, intercept = np.polyfit(idx, val, 1)
    resid = val - (intercept + slope * idx)
    print('%s: %d flat edges  DX_fit = %.2f (R = %.2f)  x0_fit = %.2f  '
          'max resid %.2f  rms %.2f'
          % (name, len(pts), slope, slope / 1.5, intercept,
             np.abs(resid).max(), np.sqrt((resid ** 2).mean())))
