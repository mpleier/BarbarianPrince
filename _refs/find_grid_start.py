#!/usr/bin/env python
"""Find where the hex grid actually starts in the one-piece scan."""
import numpy as np
from PIL import Image

A = np.asarray(Image.open('_refs/barbarianprince_onepiecemap-revc.jpg'))
print(f"Image shape: {A.shape}")

# Sample a row near the top to find the sidebar boundary
print("\nSampling row at y=90 (near top of hex grid):")
for x in range(150, 450, 10):
    px = A[90, x]
    print(f"  x={x}: RGB={px}")