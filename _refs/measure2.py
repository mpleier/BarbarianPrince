"""Find the long horizontal white grid edges to measure the true row pitch."""
import numpy as np
from PIL import Image

for name in ('map1.jpg', 'map2.jpg'):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    H, W = A.shape[:2]
    white = (A.min(axis=2) > 210)
    ys = []
    for y in range(H):
        row = white[y]
        # longest run
        best = 0
        cur = 0
        for v in row:
            if v:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        if best >= 70:
            ys.append(y)
    # cluster consecutive ys
    clusters = []
    for y in ys:
        if clusters and y == clusters[-1][-1] + 1:
            clusters[-1].append(y)
        else:
            clusters.append([y])
    centres = [sum(c) / len(c) for c in clusters]
    diffs = [round(centres[i + 1] - centres[i], 1) for i in range(len(centres) - 1)]
    print(name, 'H=', H)
    print('  edge y:', [round(c, 1) for c in centres[:20]])
    print('  diffs  :', diffs[:20])
    print()
