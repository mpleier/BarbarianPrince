"""Classify the pixels along several rows near the board's left edge so the
leftmost extent of the printed board can be located."""
import numpy as np
from PIL import Image

A = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)

for y in (40, 60, 80, 98, 120, 140, 160, 190):
    line = ''
    for x in range(200, 460):
        r, g, b = A[y, x]
        mx, mn = max(r, g, b), min(r, g, b)
        if mx < 120:
            line += '#'
        elif mx - mn > 40:
            line += '.'
        else:
            line += ' '
    print('%3d %s' % (y, line))












