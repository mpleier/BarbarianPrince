#!/usr/bin/env python
"""Debug hex centers and pixel values for the one-piece scan."""
import numpy as np
from PIL import Image
import math

A = np.asarray(Image.open('_refs/barbarianprince_onepiecemap-revc.jpg'))
print(f"Image shape: {A.shape}")

R = 81.0
DX = 1.5 * R
DY = math.sqrt(3) * R
SCAN_X0 = 111.0
SCAN_Y0 = 78.1481

def centre(col, row):
    i = col - 1
    return (SCAN_X0 + DX * i,
            SCAN_Y0 + DY * (row - 1) + (i % 2) * DY / 2.0)

print("\nHex centers and pixel values:")
for col in range(1, 6):
    for row in range(1, 6):
        cx, cy = centre(col, row)
        cx, cy = int(cx), int(cy)
        if 0 <= cy < A.shape[0] and 0 <= cx < A.shape[1]:
            px = A[cy, cx]
            print(f"  Hex {col:02d}{row:02d}: center=({cx},{cy}) RGB={px}")
        else:
            print(f"  Hex {col:02d}{row:02d}: center=({cx},{cy}) OUT OF BOUNDS")

# Check if there's an alpha channel issue
print("\nImage mode:", Image.open('_refs/barbarianprince_onepiecemap-revc.jpg').mode)

# Check what the content detection found
gray = A.mean(axis=2)
THRESH = 200
nonwhite = gray < THRESH
rows_c = np.where(nonwhite.any(axis=1))[0]
cols_c = np.where(nonwhite.any(axis=0))[0]
print(f"\nContent detection:")
print(f"  Content rows: {rows_c[0]} - {rows_c[-1]}")
print(f"  Content cols: {cols_c[0]} - {cols_c[-1]}")
