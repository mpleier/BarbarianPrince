"""Visualize the model's rivers and roads overlaid on Cleanedmap.jpg for comparison."""
import json
import os
import math
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'data')

# Load features
with open(os.path.join(DATA, 'features.json'), encoding='utf-8') as f:
    feats = json.load(f)

# Load hex grid for centres
with open(os.path.join(ROOT, 'hexes.json'), encoding='utf-8') as f:
    hexes_data = json.load(f)

hexes = {h['id']: h for h in hexes_data}

# Hex geometry (from geometry.py)
R = 106.0
SQ3 = math.sqrt(3.0)
DX = 1.5 * R
DY = SQ3 * R

def hex_centre(col, row):
    """Pixel centre of a hex in the stitched board (map1 frame)."""
    i = col - 1
    x = 377.0 + DX * i
    y = 98.2 + DY * (row - 1) + (i % 2) * DY / 2.0
    return (x, y)

def hex_corners(col, row):
    cx, cy = hex_centre(col, row)
    return [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]

# Open Cleanedmap.jpg
img_path = os.path.join(ROOT, 'Cleanedmap.jpg')
img = Image.open(img_path)
draw = ImageDraw.Draw(img)

# --- Draw rivers (thick blue lines between river-side neighbours) ---
river_sides = [tuple(sorted(p)) for p in feats['river_sides']]
road_sides = [tuple(sorted(p)) for p in feats['road_sides']]

def parse_hex(hid):
    return int(hid[:2]), int(hid[2:])

# For each river side, draw a line between the two hex centres
for a, b in river_sides:
    col_a, row_a = parse_hex(a)
    col_b, row_b = parse_hex(b)
    # Find the shared edge midpoint
    corners_a = hex_corners(col_a, row_a)
    corners_b = hex_corners(col_b, row_b)
    # Find common edge - shared vertices
    shared = []
    for ca in corners_a:
        for cb in corners_b:
            if abs(ca[0] - cb[0]) < 2 and abs(ca[1] - cb[1]) < 2:
                shared.append(ca)
    if len(shared) >= 2:
        # Draw along the shared edge
        draw.line([shared[0], shared[1]], fill=(255, 0, 255, 128), width=6)

# --- Draw roads (thick orange-red lines between road-side neighbours) ---
for a, b in road_sides:
    col_a, row_a = parse_hex(a)
    col_b, row_b = parse_hex(b)
    corners_a = hex_corners(col_a, row_a)
    corners_b = hex_corners(col_b, row_b)
    shared = []
    for ca in corners_a:
        for cb in corners_b:
            if abs(ca[0] - cb[0]) < 2 and abs(ca[1] - cb[1]) < 2:
                shared.append(ca)
    if len(shared) >= 2:
        draw.line([shared[0], shared[1]], fill=(255, 165, 0, 180), width=6)

# --- Also highlight road hexes (small circles) ---
for hid in feats['road_hexes']:
    col, row = parse_hex(hid)
    cx, cy = hex_centre(col, row)
    draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(0, 255, 0, 128))

# Save overlay
out_path = os.path.join(ROOT, 'check_roads_rivers_overlay.jpg')
img.save(out_path, quality=92)
print(f'Saved overlay to {out_path}')
print(f'River sides modelled: {len(river_sides)}')
print(f'Road sides modelled: {len(road_sides)}')
print(f'Road hexes modelled: {len(feats["road_hexes"])}')

# Print hex centres vs image centre for calibration check
img_cx, img_cy = img.size[0] / 2, img.size[1] / 2
print(f'Image size: {img.size}')
print(f'Image centre: ({img_cx:.0f}, {img_cy:.0f})')

# Check corner hexes - the map shows hex IDs printed on them
# Hex 0101 should be at top-left, hex 2023 at bottom-right
c1 = hex_centre(1, 1)
c2 = hex_centre(20, 23)
print(f'Hex 0101 centre in model: {c1}')
print(f'Hex 2023 centre in model: {c2}')
print(f'Model board width: {c2[0] - c1[0]:.0f}px')
print(f'Model board height: {c2[1] - c1[1]:.0f}px')
