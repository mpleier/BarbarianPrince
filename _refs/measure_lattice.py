"""Measure the true hex lattice from the white grid lines in each scan."""
import numpy as np
from PIL import Image

for name in ('map1.jpg', 'map2.jpg'):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    H, W = A.shape[:2]
    white = (A.min(axis=2) > 215)
    # vertical scan line through column 1 (x ~ 377) and column 3 (x ~ 665)
    for x in (377, 536, 695, 854):
        col = white[:, x]
        ys = [y for y in range(H) if col[y]]
        # group consecutive
        runs = []
        for y in ys:
            if runs and y == runs[-1][1] + 1:
                runs[-1][1] = y
            else:
                runs.append([y, y])
        print(name, 'x=%d' % x, 'white runs:', [ (a+b)//2 for a, b in runs if b-a < 6 ][:14])
    print()
