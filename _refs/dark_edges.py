"""Locate the printed hex edges as runs of DARK pixels of length ~ R (vectorised)."""
import math
import numpy as np
from PIL import Image

R = 106.0


def runs(row):
    """Return (start, end) of every maximal True run in a 1-D bool array."""
    idx = np.flatnonzero(np.diff(np.r_[0, row.astype(np.int8), 0]))
    return [(idx[i], idx[i + 1] - 1) for i in range(0, len(idx), 2)]


for name in ('map1.jpg', 'map2.jpg'):
    A = np.asarray(Image.open('_refs/' + name).convert('L'), dtype=np.int16)
    dark = A < 150
    print('===', name)
    out = []
    for y in range(A.shape[0]):
        segs = [(s, e) for s, e in runs(dark[y]) if 90 <= e - s + 1 <= 120]
        if segs:
            out.append((y, segs))
    for y, segs in out[:16]:
        print('  y=%6.1f  %s' % (y, ', '.join(
            '%.1f..%.1f len=%d mid=%.1f' % (s, e, e - s + 1, (s + e) / 2)
            for s, e in segs[:8])))
    print()
