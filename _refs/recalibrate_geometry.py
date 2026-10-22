#!/usr/bin/env python
"""Final verification of geometry and terrain classification."""
import sys
sys.path.insert(0, 'src')
import geometry as geo
import numpy as np
from PIL import Image
import json

A = np.asarray(Image.open('_refs/barbarianprince_onepiecemap-revc.jpg'))
H, W = A.shape[:2]
hexes = json.load(open('_refs/hexes.json'))

print(f"Image: {W}x{H}")
print(f"Geometry: R={geo.R}, SCAN_X0={geo.SCAN_X0}, SCAN_Y0={geo.SCAN_Y0}")
print()

# 1. All hexes fit
out_of_bounds = 0
for col in range(1, 21):
    for row in range(1, 24):
        cx, cy = geo.centre(col, row)
        if cy < 0 or cy >= H or cx < 0 or cx >= W:
            out_of_bounds += 1
print(f"1. All hexes within bounds: {'PASS' if out_of_bounds == 0 else 'FAIL'} ({out_of_bounds} out of bounds)")

# 2. Count bad center pixels (white/black)
bad_centers = 0
for col in range(1, 21):
    for row in range(1, 24):
        cx, cy = int(geo.centre(col, row)[0]), int(geo.centre(col, row)[1])
        px = A[cy, cx]
        if px[0] > 240 and px[1] > 240 and px[2] > 240:
            bad_centers += 1
print(f"2. Bad center pixels (white): {bad_centers}/460 ({bad_centers/460*100:.1f}%)")

# 3. Terrain distribution
from collections import Counter
counts = Counter(h['terrain'] for h in hexes)
print(f"3. Terrain distribution:")
for t, c in counts.most_common():
    print(f"   {t:12}: {c:3d} ({c/460*100:.1f}%)")

# 4. Verify hex 0101 is farmland (Ogon)
h0101 = next(h for h in hexes if h['id'] == '0101')
print(f"4. Hex 0101 terrain: {h0101['terrain']} {'PASS' if h0101['terrain'] == 'farmland' else 'FAIL'}")

# 5. Check neighbours work for a few hexes
print(f"5. Neighbour check:")
for hid in ['0101', '1012', '2023']:
    col, row = int(hid[:2]), int(hid[2:])
    neighbors = geo.neighbours(col, row)
    print(f"   {hid}: {len(neighbors)} neighbours {', '.join(f'{k}={v}' for k,v in neighbors.items())}")

# 6. Verify neighbour consistency (if A is B's neighbor, B should be A's neighbor)
print(f"6. Neighbour consistency check:")
inconsistent = 0
hex_set = {h['id'] for h in hexes}
for h in hexes:
    col, row = h['col'], h['row']
    for dir_name, neighbor_id in geo.neighbours(col, row).items():
        nc, nr = int(neighbor_id[:2]), int(neighbor_id[2:])
        # Check if this hex is in the neighbor's neighbor list
        neighbor_neighbors = geo.neighbours(nc, nr)
        if h['id'] not in neighbor_neighbors.values():
            inconsistent += 1
            if inconsistent <= 5:
                print(f"   INCONSISTENT: {h['id']} -> {neighbor_id} but {neighbor_id} doesn't have {h['id']}")
print(f"   Total inconsistencies: {inconsistent}")