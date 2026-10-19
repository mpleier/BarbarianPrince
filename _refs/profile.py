"""Print the white-line profile across a known hex boundary to check offsets."""
import numpy as np
from PIL import Image

A = np.asarray(Image.open('_refs/map1.jpg').convert('RGB'), dtype=np.int16)
white = (A.min(axis=2) > 200)
for y in range(180, 202):
    print(y, ''.join('#' if v else '.' for v in white[y, 300:460]))
