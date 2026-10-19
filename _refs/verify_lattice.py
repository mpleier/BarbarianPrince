"""Quantify how well the model lattice matches the printed grid lines.

For every hex edge we sample points along the edge and measure the fraction
that land on a printed white line (within a few pixels). A correct lattice
scores high; a wrong origin scores low.
"""
import math
import sys

import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)
R = 106.0
DY = SQ3 * R
DX = 1.5 * R

EDGE_TOL = 6          # px either side of the modelled edge
SAMPLES = 25          # samples along each edge


def white_mask(path):
    A = np.asarray(Image.open(path).convert('RGB'), dtype=np.int16)
    return A.min(axis=2) > 200


def edge_points(cx, cy, a, b):
    """Points along the segment between two hex vertices."""
    return [(cx + (b[0] - cx) * t, cy + (b[1] - cy) * t)
            for t in np.linspace(0.15, 0.85, SAMPLES)]


def score(mask, x0, y0, rows, cols):
    hits = total = 0
    for c in cols:
        i = c - 1
        for r in rows:
            cx = x0 + DX * i
            cy = y0 + DY * (r - rows[0]) + (i % 2) * DY / 2.0
            verts = [(cx + R * math.cos(math.radians(a)),
                      cy + R * math.sin(math.radians(a))) for a in range(0, 360, 60)]
            for k in range(6):
                a, b = verts[k], verts[(k + 1) % 6]
                for px, py in edge_points(cx, cy, a, b):
                    x, y = int(round(px)), int(round(py))
                    H, W = mask.shape
                    if not (0 <= x < W and 0 <= y < H):
                        continue
                    window = mask[max(0, y - EDGE_TOL):y + EDGE_TOL + 1,
                                  max(0, x - EDGE_TOL):x + EDGE_TOL + 1]
                    total += 1
                    if window.any():
                        hits += 1
    return hits / total if total else 0.0


def main():
    m1 = white_mask('_refs/map1.jpg')
    m2 = white_mask('_refs/map2.jpg')
    cols = list(range(1, 21))

    print('map1.jpg  (rows 1-12)')
    best = None
    for y0 in [94, 96, 98, 98.7, 100, 102]:
        for x0 in [373, 375, 377, 379, 381]:
            s = score(m1, x0, y0, range(1, 13), cols)
            if best is None or s > best[0]:
                best = (s, x0, y0)
            print('   x0=%5.1f y0=%5.1f  edge-hit=%.3f' % (x0, y0, s))
    print('   best:', best)

    print('map2.jpg  (rows 13-23)')
    best2 = None
    for y0 in [199, 201, 203.3, 205, 207]:
        for x0 in [373, 375, 377, 379, 381]:
            s = score(m2, x0, y0, range(13, 24), cols)
            if best2 is None or s > best2[0]:
                best2 = (s, x0, y0)
            print('   x0=%5.1f y0=%5.1f  edge-hit=%.3f' % (x0, y0, s))
    print('   best:', best2)


if __name__ == '__main__':
    main()
