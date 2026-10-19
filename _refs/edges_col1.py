"""Detect the flat top/bottom edges of column-1 hexes directly."""
import numpy as np
from PIL import Image

R = 106.0
for name, x0 in (('map1.jpg', 377), ('map2.jpg', 377)):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    H, W = A.shape[:2]
    lo, hi = int(x0 - R / 2), int(x0 + R / 2)
    ys = []
    for y in range(H):
        seg = white[y, lo:hi]
        if seg.mean() > 0.85:
            ys.append(y)
    clusters = []
    for y in ys:
        if clusters and y == clusters[-1][-1] + 1:
            clusters[-1].append(y)
        else:
            clusters.append([y])
    centres = [sum(c) / len(c) for c in clusters]
    print(name, 'H=', H, 'x0=', x0)
    print('  edge ys:', [round(c, 1) for c in centres])
    print('  diffs  :', [round(centres[i + 1] - centres[i], 1) for i in range(len(centres) - 1)])
    print()
