"""Find the left/right extent of the printed board in each scan."""
import numpy as np
from PIL import Image

for name in ('map1.jpg', 'map2.jpg'):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    nonwhite = (A.min(axis=2) < 235)
    cols = nonwhite.mean(axis=0)
    W = len(cols)
    left = next(i for i in range(W) if cols[i] > 0.05)
    right = next(i for i in range(W - 1, -1, -1) if cols[i] > 0.05)
    print('%s: board spans x = %d .. %d  (width %d)' % (name, left, right, right - left + 1))
