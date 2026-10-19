"""At the seam line, find the x-extent of every printed flat hex edge and
compare it with the model's predicted flat-edge spans."""
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, R, DX, DY, BOARD_Y_OFF, SEAM_Y

im1 = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
im2 = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
off2 = int(round(BOARD_Y_OFF['map2.jpg']))
H = max(im1.shape[0], im2.shape[0] + off2)
board = np.full((H, im1.shape[1], 3), 255, dtype=np.int16)
board[:im1.shape[0]] = im1
board[off2:off2 + im2.shape[0]] = im2

y = int(round(SEAM_Y))
row = board[y - 2:y + 3].min(axis=2).mean(axis=0)
white = row > 200

runs = []
start = None
for x, w in enumerate(white):
    if w and start is None:
        start = x
    elif not w and start is not None:
        runs.append((start, x - 1))
        start = None
if start is not None:
    runs.append((start, len(white) - 1))

print('printed flat-edge runs at the seam (y = %d):' % y)
model = []
for c in range(1, NC + 1):
    i = c - 1
    cx = 377.0 + DX * i
    model.append((c, cx - R / 2.0, cx + R / 2.0))

for a, b in runs:
    if b - a + 1 < 30:
        continue
    mid = (a + b) / 2.0
    best = min(model, key=lambda m: abs(m[1] + R / 2 - mid) if False else abs((m[1] + m[2]) / 2 - mid))
    err = mid - (best[1] + best[2]) / 2.0
    print('   x = %4d..%4d  (centre %.1f)  nearest model col %2d centre %.1f  err %+.1f'
          % (a, b, mid, best[0], (best[1] + best[2]) / 2.0, err))
