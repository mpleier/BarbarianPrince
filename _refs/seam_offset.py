"""Measure the printed board extents and render the seam region with the current
BOARD_Y_OFF so the stitch can be inspected visually."""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import R, DX, DY, SCANS, BOARD_Y_OFF, SEAM_Y, NC, NR

im1 = Image.open('_refs/map1.jpg').convert('RGB')
im2 = Image.open('_refs/map2.jpg').convert('RGB')
A1 = np.asarray(im1, dtype=np.int16)
A2 = np.asarray(im2, dtype=np.int16)

white = A1.min(axis=2) > 200

# --- where does the printed board actually start/end? ---
col = 377
ys = [y for y in range(A1.shape[0]) if not white[y, col - 30:col + 30].all()]
print('map1: first non-white row at x=377 -> y = %d' % (ys[0] if ys else -1))

col2 = 377
w2 = A2.min(axis=2) > 200
ys2 = [y for y in range(A2.shape[0]) if not w2[y, col2 - 30:col2 + 30].all()]
print('map2: first non-white row at x=377 -> y = %d' % (ys2[0] if ys2 else -1))
print('map2: last  non-white row at x=377 -> y = %d' % (ys2[-1] if ys2 else -1))

row = 1000
xs = [x for x in range(A1.shape[1]) if not white[row, x].all()]
print('map1 at y=1000: content x = %d .. %d' % (xs[0], xs[-1]))

# --- render the seam ---
off = int(round(BOARD_Y_OFF['map2.jpg']))
H = off + A2.shape[0]
board = np.full((H, A1.shape[1], 3), 255, dtype=np.uint8)
board[:A1.shape[0]] = np.asarray(im1, dtype=np.uint8)
board[off:off + A2.shape[0]] = np.asarray(im2, dtype=np.uint8)

crop = board[int(SEAM_Y) - 260:int(SEAM_Y) + 260, 300:1100]
Image.fromarray(crop).resize((1600, 1040)).save('_refs/seam_zoom.png')
print('wrote _refs/seam_zoom.png  (unified y %d..%d, x 300..1100)'
      % (int(SEAM_Y) - 260, int(SEAM_Y) + 260))
print('SEAM_Y = %.2f, BOARD_Y_OFF = %.2f' % (SEAM_Y, BOARD_Y_OFF['map2.jpg']))


