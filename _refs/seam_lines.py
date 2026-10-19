"""Detect the printed horizontal grid lines in the stitched board around the
seam, in the column-1 flat-edge band (x = 324..430), and compare with SEAM_Y."""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, R, DX, DY, SCANS, BOARD_Y_OFF, SEAM_Y

im1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
im2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
off2 = int(round(BOARD_Y_OFF['map2.jpg']))
H = max(im1.shape[0], im2.shape[0] + off2)
board = np.full((H, im1.shape[1], 3), 255, dtype=np.int16)
board[:im1.shape[0]] = im1
board[off2:off2 + im2.shape[0]] = im2

band = board[1900:2500, 324:431]
white = band.min(axis=2) > 200
frac = white.mean(axis=1)
print('unified y : fraction of the column-1 flat edge that is white')
runs = []
for i, f in enumerate(frac):
    y = 1900 + i
    if f > 0.5:
        runs.append((y, f))
# collapse runs
groups = []
for y, f in runs:
    if groups and y == groups[-1][1] + 1:
        groups[-1] = (groups[-1][0], y, (groups[-1][2] + f) / 2)
    else:
        groups.append((y, y, f))
for a, b, f in groups:
    print('   line y = %6.1f  (span %d px, mean white %.2f)' % ((a + b) / 2.0, b - a + 1, f))
print('SEAM_Y = %.2f' % SEAM_Y)
