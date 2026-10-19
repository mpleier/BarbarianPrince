"""Check the column lattice by measuring the x-extent of the printed flat hex
edges on a known horizontal grid line in each scan."""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, R, DX, SCANS, DY

SQ3 = 3 ** 0.5


def runs_at(A, y, min_len=30):
    row = A[max(0, y - 2):y + 3].min(axis=2).mean(axis=0)
    white = row > 200
    out, start = [], None
    for x, w in enumerate(white):
        if w and start is None:
            start = x
        elif not w and start is not None:
            if x - start >= min_len:
                out.append((start, x - 1))
            start = None
    if start is not None and len(white) - start >= min_len:
        out.append((start, len(white) - 1))
    return out


for name, y_line, row_of_line in (
        ('map1.jpg', 2027, 11),      # row 11 / row 12 boundary
        ('map2.jpg', 111, 12)):      # row 12 / row 13 boundary
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    p = SCANS[name]
    print('=== %s  flat edges on the line y = %d' % (name, y_line))
    for a, b in runs_at(A, y_line):
        mid = (a + b) / 2.0
        # the flat edge belongs to the column whose axis is at mid
        col = round((mid - p['x0']) / DX) + 1
        if 1 <= col <= NC:
            pred_c = p['x0'] + DX * (col - 1)
            pred_lo, pred_hi = pred_c - R / 2.0, pred_c + R / 2.0
            print('   edge x=%4d..%4d  len %3d  -> col %2d  model %6.1f..%6.1f  '
                  'errL %+.1f errR %+.1f' % (a, b, b - a + 1, col, pred_lo, pred_hi,
                                            a - pred_lo, b - pred_hi))
