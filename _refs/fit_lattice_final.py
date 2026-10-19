"""Least-squares fit of the hex lattice to the printed grid lines.

Detects:
  * horizontal grid lines in the column-1 band (x = 340..410)  -> row pitch
  * clean flat edges (length ~ R) across the whole scan        -> column pitch
and fits  y = y0 + DY*(row - first)  and  x = x0 + DX*(col - 1).
"""
import math
import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)


def h_lines(mask, xlo=340, xhi=410, thresh=0.9):
    band = mask[:, xlo:xhi]
    frac = band.mean(axis=1)
    out, y, H = [], 0, len(frac)
    while y < H:
        if frac[y] > thresh:
            s = y
            while y < H and frac[y] > thresh:
                y += 1
            out.append((s + y - 1) / 2.0)
        else:
            y += 1
    return out


def v_centres(mask, lo=96, hi=116):
    centres = []
    H, W = mask.shape
    for y in range(H):
        row = mask[y]
        x = 0
        while x < W:
            if row[x]:
                s = x
                while x < W and row[x]:
                    x += 1
                e = x - 1
                if lo <= e - s + 1 <= hi:
                    centres.append((s + e) / 2.0)
            else:
                x += 1
    centres.sort()
    groups = []
    for c in centres:
        if groups and c - groups[-1][-1] <= 3:
            groups[-1].append(c)
        else:
            groups.append([c])
    return [float(np.mean(g)) for g in groups if len(g) >= 4]


def ls(xs, ys):
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    slope, intercept = np.polyfit(xs, ys, 1)
    resid = ys - (slope * xs + intercept)
    return slope, intercept, float(np.abs(resid).max()), float(np.mean(np.abs(resid)))


for name, first_row in (('map1.jpg', 1), ('map2.jpg', 13)):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    mask = A.min(axis=2) > 200
    hl = h_lines(mask)
    print(name)
    print('  horizontal lines:', [round(v, 1) for v in hl])
    rows = list(range(first_row, first_row + len(hl)))
    p, b, mx, mn = ls(rows, hl)
    print('  row pitch = %.3f  (R = %.2f)  max|resid| = %.2f' % (p, p / SQ3, mx))
    # y0 = value at row first_row
    y0 = b + p * first_row
    print('  fitted y0 = %.2f' % y0)

    vc = v_centres(mask)
    print('  column centres:', [round(v, 1) for v in vc])
    if vc:
        # assume consecutive columns starting at some c; try every start
        best = None
        for c0 in range(1, 21):
            cols = [c0 + i for i in range(len(vc))]
            s, i2, mx2, mn2 = ls(cols, vc)
            if best is None or mn2 < best[3]:
                best = (s, i2, mx2, mn2, c0)
        s, i2, mx2, mn2, c0 = best
        print('  col pitch = %.3f  (R = %.2f)  x at col1 = %.2f  max|resid| = %.2f'
              % (s, s / 1.5, i2 + s, mx2))
    print()
