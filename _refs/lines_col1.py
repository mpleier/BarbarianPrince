"""List every horizontal grid line in column 1 of each scan (x = 340..410)."""
import numpy as np
from PIL import Image

for name in ('map1.jpg', 'map2.jpg'):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    band = white[:, 340:410]
    frac = band.mean(axis=1)
    runs = []
    y = 0
    H = len(frac)
    while y < H:
        if frac[y] > 0.9:
            s = y
            while y < H and frac[y] > 0.9:
                y += 1
            runs.append((s + y - 1) / 2.0)
        else:
            y += 1
    print(name, 'line centres:', runs)
    if len(runs) > 1:
        d = [runs[i + 1] - runs[i] for i in range(len(runs) - 1)]
        print('   pitches:', [round(x, 1) for x in d], 'mean=%.2f' % np.mean(d))
    print()
