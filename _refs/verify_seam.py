"""Re-measure the stitch seam and the board extents straight from the scans and
compare them with the constants in src/geometry.py.

Run:  python _refs/verify_seam.py
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'src')
sys.path.insert(0, SRC)

from geometry import (R, DX, DY, SQ3, SCANS, BOARD_Y_OFF, SEAM_Y, NC, NR,
                      board_bounds)

BAND = (324, 431)          # column-1 flat-edge band


def printed_lines(path, band=BAND, thresh=0.9):
    """Centres of the horizontal white grid lines inside `band`.

    The band is only ~107 px wide (the flat top/bottom edge of column 1), so a
    real grid line is white across essentially the whole band; label text and
    map artwork only whiten part of it.
    """
    A = np.asarray(Image.open(path).convert('RGB'), dtype=np.int16)
    white = A.min(axis=2) > 200
    frac = white[:, band[0]:band[1]].mean(axis=1)
    out, y = [], 0
    while y < A.shape[0]:
        if frac[y] > thresh:
            y0 = y
            while y < A.shape[0] and frac[y] > thresh:
                y += 1
            out.append((y0 + y - 1) / 2.0)
        else:
            y += 1
    return out


def printed_columns(path, band, thresh=0.9):
    """Centres of the vertical grid lines crossing the horizontal band `band`."""
    A = np.asarray(Image.open(path).convert('RGB'), dtype=np.int16)
    white = A.min(axis=2) > 200
    frac = white[band[0]:band[1], :].mean(axis=0)
    out, x = [], 0
    while x < A.shape[1]:
        if frac[x] > thresh:
            x0 = x
            while x < A.shape[1] and frac[x] > thresh:
                x += 1
            out.append((x0 + x - 1) / 2.0)
        else:
            x += 1
    return out


def flat_edges(path, y, min_len=90):
    """Centres of the white runs along the horizontal scan line `y`.

    On a row boundary only the *even* columns have a flat hex edge (R px long)
    centred on the column axis, so the long white runs there pin the column
    pitch and the column origin.
    """
    A = np.asarray(Image.open(path).convert('RGB'), dtype=np.int16)
    row = A.min(axis=2)[y] > 200
    out, x = [], 0
    while x < row.size:
        if row[x]:
            x0 = x
            while x < row.size and row[x]:
                x += 1
            if x - x0 >= min_len:
                out.append((x0 + x - 1) / 2.0)
        else:
            x += 1
    return out


def main():
    print('constants: R=%.1f DX=%.3f DY=%.3f' % (R, DX, DY))
    print('SCANS   : %s' % SCANS)
    print('BOARD_Y_OFF = %s' % BOARD_Y_OFF)
    print('SEAM_Y      = %.2f' % SEAM_Y)
    print()

    for scan, cfg in SCANS.items():
        y0 = cfg['y0']
        first, last = cfg['first_row'], cfg['last_row']
        lines = printed_lines(os.path.join(HERE, scan))
        # Printed horizontal lines inside the board: the boundary between
        # row k and row k+1, for k = first .. last-1, expressed in the scan's
        # own (local) pixel frame.
        model = [(first - 1, y0 - DY / 2.0)] + \
                [(k, y0 + DY * (k - first) + DY / 2.0) for k in range(first, last)]
        print('%s: %d printed grid lines detected in the column-1 band'
              % (scan, len(lines)))
        errs = []
        matched = []
        for k, pred in model:
            best = min(lines, key=lambda v: abs(v - pred))
            err = pred - best
            if abs(err) < 12:
                errs.append(err)
                matched.append((k, best))
            print('   row %2d/%2d boundary: model %8.2f  printed %8.1f  err %+.2f'
                  % (k, k + 1, pred, best, err))
        if len(matched) >= 2:
            ks = [k for k, _ in matched]
            vs = [v for _, v in matched]
            n = len(matched)
            kb = sum(ks) / n
            vb = sum(vs) / n
            pitch = sum((k - kb) * (v - vb) for k, v in zip(ks, vs)) / \
                    sum((k - kb) ** 2 for k in ks)
            print('   measured row pitch: %.2f px (DY = %.2f, R = %.2f)'
                  % (pitch, DY, pitch / SQ3))
        print('   max |row residual|: %.2f px' % max(abs(e) for e in errs))
        print()

    # Column pitch: the flat edges on a row boundary are R px long and centred
    # on the column axis, so their centres pin DX and x0.
    print('column pitch check (flat hex edges on row boundaries, map1.jpg):')
    residuals = []
    for k in (1, 3, 5, 7, 9, 10):
        y = int(round(SCANS['map1.jpg']['y0'] + DY * k + DY / 2.0))
        for c in flat_edges(os.path.join(HERE, 'map1.jpg'), y):
            i = round((c - SCANS['map1.jpg']['x0']) / DX)
            if 0 <= i < NC and i % 2 == 0:
                err = c - (SCANS['map1.jpg']['x0'] + DX * i)
                if abs(err) < 10:
                    residuals.append(err)
                    print('   y=%5d  edge centre %8.1f  column %2d  err %+.2f'
                          % (y, c, i + 1, err))
    if residuals:
        mean = sum(residuals) / len(residuals)
        print('   mean column error %.2f px, max %.2f px  -> x0 = %.1f is solid'
              % (mean, max(abs(r) for r in residuals), SCANS['map1.jpg']['x0']))
    print()

    # The seam: map1's 11/12 boundary line and map2's 12/13 boundary line are
    # the same printed line, so both frames must agree on its unified y.
    seam_map1 = SCANS['map1.jpg']['y0'] + DY * 11 + DY / 2.0
    seam_map2 = SCANS['map2.jpg']['y0'] - DY / 2.0 + BOARD_Y_OFF['map2.jpg']
    print('seam line: map1 frame %.2f, map2 frame %.2f, SEAM_Y %.2f'
          % (seam_map1, seam_map2, SEAM_Y))
    lines2 = printed_lines(os.path.join(HERE, 'map2.jpg'))
    seam_local = SEAM_Y - BOARD_Y_OFF['map2.jpg']
    best = min(lines2, key=lambda v: abs(v - seam_local))
    print('seam vs printed 12/13 line: local %.1f (unified %.1f) -> err %+.2f px'
          % (best, best + BOARD_Y_OFF['map2.jpg'], seam_local - best))

    minx, miny, maxx, maxy = board_bounds()
    print('lattice extents: x %.1f..%.1f   y %.1f..%.1f' % (minx, maxx, miny, maxy))

    A1 = np.asarray(Image.open(os.path.join(HERE, 'map1.jpg')).convert('RGB'),
                    dtype=np.int16)
    A2 = np.asarray(Image.open(os.path.join(HERE, 'map2.jpg')).convert('RGB'),
                    dtype=np.int16)
    chroma1 = (A1.max(axis=2) - A1.min(axis=2)) > 25
    ys, xs = np.nonzero(chroma1)
    print('map1 coloured content: x %d..%d  y %d..%d' % (xs.min(), xs.max(),
                                                         ys.min(), ys.max()))
    chroma2 = (A2.max(axis=2) - A2.min(axis=2)) > 25
    ys2, xs2 = np.nonzero(chroma2)
    print('map2 coloured content: x %d..%d  y %d..%d (unified y %d..%d)'
          % (xs2.min(), xs2.max(), ys2.min(), ys2.max(),
             ys2.min() + BOARD_Y_OFF['map2.jpg'],
             ys2.max() + BOARD_Y_OFF['map2.jpg']))
    print('scan sizes: map1 %dx%d, map2 %dx%d' % (A1.shape[1], A1.shape[0],
                                                  A2.shape[1], A2.shape[0]))


if __name__ == '__main__':
    main()
