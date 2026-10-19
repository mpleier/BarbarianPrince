"""Find the stitch offset by cross-correlating the two scans where they overlap."""
import numpy as np
from PIL import Image

a1 = np.asarray(Image.open('_refs/map1.jpg').convert('L'), dtype=np.float32)
a2 = np.asarray(Image.open('_refs/map2.jpg').convert('L'), dtype=np.float32)
H1, W1 = a1.shape
H2, W2 = a2.shape
W = min(W1, W2)
a1 = a1[:, :W]
a2 = a2[:, :W]

best = None
for off in range(1900, 2300):
    # rows y in [off, H1) are covered by both scans
    lo = off
    hi = min(H1, off + H2)
    if hi - lo < 40:
        continue
    d = np.abs(a1[lo:hi] - a2[lo - off:hi - off]).mean()
    if best is None or d < best[0]:
        best = (round(float(d), 3), off)
print('best offset by pixel match:', best)

for off in range(1990, 2110, 10):
    lo = off
    hi = min(H1, off + H2)
    d = np.abs(a1[lo:hi] - a2[lo - off:hi - off]).mean()
    print('  off=%d overlap=%d rows mad=%.3f' % (off, hi - lo, d))
