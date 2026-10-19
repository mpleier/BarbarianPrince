"""Cross-correlate the two scans in the seam region to pin the stitch offset."""
import numpy as np
from PIL import Image

A1 = np.asarray(Image.open('_refs/map1.jpg').convert('L'), dtype=np.float32)
A2 = np.asarray(Image.open('_refs/map2.jpg').convert('L'), dtype=np.float32)

H1, W1 = A1.shape
H2, W2 = A2.shape
print('map1', (W1, H1), 'map2', (W2, H2))

# compare map1 rows [lo, H1) against map2 rows [lo-off, H2-off)
best = None
for off in range(2040, 2160):
    lo = max(0, off)
    hi = min(H1, off + H2)
    if hi - lo < 20:
        continue
    a = A1[lo:hi]
    b = A2[lo - off:hi - off]
    n = min(a.shape[0], b.shape[0])
    a, b = a[:n], b[:n]
    mad = np.abs(a - b).mean()
    if best is None or mad < best[1]:
        best = (off, mad, n)
    if off % 10 == 0:
        print('  off=%d overlap=%d MAD=%.2f' % (off, n, mad))
print('best:', best)
