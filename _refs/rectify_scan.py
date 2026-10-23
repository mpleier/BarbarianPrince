"""Rectify the perspective of the board photograph.

``_refs/BPMap.jpg`` is a photograph of the board, so the printed hex grid is
keystoned: the lattice drifts by up to 30 px from one corner of the image to
the other.  This script removes that distortion and writes
``_refs/BPMap_rectified.jpg``, which is the scan the game model is calibrated
against.

How the matrix was found
------------------------
1. The white hex borders were masked (bright, low saturation) and turned into
   a distance transform.
2. At 42 hexes spread over the board, the lattice centre was shifted to the
   offset that puts its six edges on the printed borders (sub-pixel residual).
   That gives a displacement field d(x, y) of the photograph's distortion.
3. A homography H mapping "position on the paper" -> "ideal lattice position"
   was fitted to those 42 correspondences by DLT (residual ~3.5 px, which is
   the noise of the local measurement).
4. The ideal lattice at the time was slightly taller than wide (RY/RX = 1.016),
   so the output is scaled by RX/RY in y as well; the result is a *regular*
   hex lattice, which is what ``src/geometry.py`` now assumes.

Run:

    python _refs/rectify_scan.py

Regenerating the file is deterministic; the model, the web app and the feature
tracer all read the rectified image.
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_refs', 'BPMap.jpg')
DST = os.path.join(ROOT, '_refs', 'BPMap_rectified.jpg')

# Paper -> ideal lattice (fitted, see the module docstring).
H = np.array([
    [0.9735490, -0.0018890, 46.183081],
    [0.0026830, 0.9870820, 12.050581],
    [-0.0000010, 0.0000000, 1.0000000],
])

# The lattice used for the fit was 1.6% taller than wide; undo that so the
# rectified image carries a regular grid.
Y_SCALE = 80.4 / 79.1

OUT_SIZE = (2440, 3237)


def rectify():
    M = np.linalg.inv(H) @ np.diag([1.0, Y_SCALE, 1.0])
    M /= M[2, 2]
    coeffs = [M[0, 0], M[0, 1], M[0, 2],
              M[1, 0], M[1, 1], M[1, 2],
              M[2, 0], M[2, 1]]
    img = Image.open(SRC).convert('RGB')
    out = img.transform(OUT_SIZE, Image.PERSPECTIVE, coeffs,
                        resample=Image.BICUBIC, fillcolor=(250, 250, 245))
    out.save(DST, quality=92)
    return DST


if __name__ == '__main__':
    path = rectify()
    print('wrote', path, Image.open(path).size)
