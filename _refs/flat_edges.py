"""Measure the flat hex edges on the printed grid lines and compare them with
the lattice model.  On a grid line, the flat edge of an odd column hex is
exactly R px long and centred on the column axis.

Run:  python _refs/flat_edges.py
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'src'))
from geometry import R, DX, DY, SCANS, NC


def runs(row, lo, hi):
    out, s = [], None
    for x in range(lo, hi):
        if row[x] and s is None:
            s = x
        elif not row[x] and s is not None:
            out.append((s, x - 1))
            s = None
    if s is not None:
        out.append((s, hi - 1))
    return out


def main():
    for name, cfg in SCANS.items():
        A = np.asarray(Image.open(os.path.join(HERE, name)).convert('RGB'),
                       dtype=np.int16)
        white = A.min(axis=2) > 190
        print('=== %s  (x0=%.1f, y0=%.1f)' % (name, cfg['x0'], cfg['y0']))
        for k in range(cfg['first_row'], cfg['last_row']):
            y = int(round(cfg['y0'] + DY * (k - cfg['first_row']) + DY / 2.0))
            if not (0 <= y < A.shape[0]):
                continue
            # Scan a generous window around the expected column-1 flat edge.
            r = runs(white[y], 250, 700)
            r = [(a, b) for a, b in r if b - a + 1 >= 60]
            print('  line y=%4d (row %2d/%2d): white runs >=60px: %s'
                  % (y, k, k + 1, r[:6]))
        print()


if __name__ == '__main__':
    main()
