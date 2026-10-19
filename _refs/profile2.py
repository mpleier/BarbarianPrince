"""Print the white-line profile in column 1 of map2 around the 12/13 boundary."""
import numpy as np
from PIL import Image

A = np.asarray(Image.open('_refs/map2.jpg').convert('RGB'), dtype=np.int16)
white = (A.min(axis=2) > 200)
for y in range(100, 130):
    print(y, ''.join('#' if v else '.' for v in white[y, 340:410]))
print()
for y in range(290, 305):
    print(y, ''.join('#' if v else '.' for v in white[y, 340:410]))
