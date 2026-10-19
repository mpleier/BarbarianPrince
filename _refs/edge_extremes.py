"""Measure the printed board's left/right extremes per scan and compare with
the lattice model in src/geometry.py.

A pixel counts as "board content" when it is either a dark grid line or a
saturated terrain colour; the surrounding page is plain white paper.

Run:  python _refs/edge_extremes.py
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'src'))
from geometry import R, DX, DY, SCANS, BOARD_Y_OFF, NC, NR, board_bounds


def content_mask(A):
    mx = A.max(axis=2)
    mn = A.min(axis=2)
    return (mx < 150) | ((mx - mn) > 30)


def main():
    minx, miny, maxx, maxy = board_bounds()
    print('model board extents: x %.1f..%.1f  y %.1f..%.1f' % (minx, miny, maxx, maxy))
    print()

    for name in ('map1.jpg', 'map2.jpg'):
        A = np.asarray(Image.open(os.path.join(HERE, name)).convert('RGB'),
                       dtype=np.int16)
        m = content_mask(A)
        ys, xs = np.nonzero(m)
        print('%s: content x %d..%d, y %d..%d' % (name, xs.min(), xs.max(),
                                                  ys.min(), ys.max()))
        # Profile at a few heights inside the board.
        for frac in (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95):
            y = int(A.shape[0] * frac)
            row = np.nonzero(m[y])[0]
            if row.size:
                print('    y=%4d  left=%4d  right=%4d' % (y, row.min(), row.max()))
        print()


if __name__ == '__main__':
    main()



if __name__ == '__main__':
    main()
