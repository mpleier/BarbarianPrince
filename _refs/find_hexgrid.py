#!/usr/bin/env python
"""Find where the actual hex grid content starts by looking for green hex colors."""
import numpy as np
from PIL import Image

A = np.asarray(Image.open('_refs/barbarianprince_onepiecemap-revc.jpg'))
print(f"Image shape: {A.shape}")

# Look for hex grid content by scanning rows for green-dominant pixels
# Green hexes have G > R and G > B
print("\nScanning for green hex content (G > R + 10 and G > B + 10):")
for y in range(50, 200, 10):
    row = A[y, :, :]
    green = (row[:, 1] > row[:, 0] + 10) & (row[:, 1] > row[:, 2] + 10)
    green_cols = np.where(green)[0]
    if len(green_cols) > 100:  # Found significant green area
        print(f"  y={y}: first green at x={green_cols[0]}, span={len(green_cols)}px")
        if y > 100:
            break

# Also check specific x positions for hex content
print("\nScanning horizontal positions for hex-like content:")
for x in range(100, 500, 50):
    col = A[100:300, x, :]
    green = (col[:, 1] > col[:, 0] + 10) & (col[:, 1] > col[:, 2] + 10)
    green_count = np.sum(green)
    print(f"  x={x}: green pixels in y=100-300: {green_count}")
