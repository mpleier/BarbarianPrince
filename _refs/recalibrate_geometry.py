#!/usr/bin/env python
"""Full verification of recalibrated geometry."""
import sys, math
sys.path.insert(0, 'src')
import geometry as geo
import numpy as np
from PIL import Image
import json

A = np.asarray(Image.open('_refs/barbarianprince_onepiecemap-revc.jpg'))
H, W = A.shape[:2]

print(f"Image: {W}x{H}")
print(f"R={geo.R}, DX={geo.DX:.2f}, DY={geo.DY:.2f}")
print(f"SCAN_X0={geo.SCAN_X0}, SCAN_Y0={geo.SCAN_Y0}")
print()

# 1. All hex centers in bounds
out_of_bounds = 0
for col in range(1, 21):
    for row in range(1, 24):
        cx, cy = geo.centre(col, row)
        if cy < 0 or cy >= H or cx < 0 or cx >= W:
            out_of_bounds += 1
print(f"1. Hex centers in bounds: {'PASS' if out_of_bounds == 0 else 'FAIL'} ({out_of_bounds}/460)")

# 2. Center pixel quality
bad_centers = 0
for col in range(1, 21):
    for row in range(1, 24):
        cx, cy = int(geo.centre(col, row)[0]), int(geo.centre(col, row)[1])
        px = A[cy, cx]
        if px[0] > 240 and px[1] > 240 and px[2] > 240:
            bad_centers += 1
print(f"2. Bad center pixels (white): {bad_centers}/460 ({bad_centers/460*100:.1f}%)")

# 3. Verify hex 0101 (Ogon) is farmland
print(f"3. Row 1 centers:")
for col in [1, 2, 3]:
    cx, cy = int(geo.centre(col, 1)[0]), int(geo.centre(col, 1)[1])
    px = A[cy, cx]
    print(f"   Hex {col:02d}01: ({cx},{cy}) RGB={px}")

# 4. Check neighbour consistency
inconsistent = 0
for col in range(1, 21):
    for row in range(1, 24):
        for dir_name, neighbor_id in geo.neighbours(col, row).items():
            nc, nr = int(neighbor_id[:2]), int(neighbor_id[2:])
            neighbor_neighbors = geo.neighbours(nc, nr)
            hid = geo.hex_id(col, row)
            if hid not in neighbor_neighbors.values():
                inconsistent += 1
print(f"4. Neighbour consistency: {'PASS' if inconsistent == 0 else 'FAIL'} ({inconsistent} inconsistencies)")

# 5. Load and verify hexes.json
hexes = json.load(open('_refs/hexes.json'))
h0101 = next(h for h in hexes if h['id'] == '0101')
print(f"5. Hex 0101 terrain: {h0101['terrain']} {'PASS' if h0101['terrain'] == 'farmland' else 'FAIL'}")