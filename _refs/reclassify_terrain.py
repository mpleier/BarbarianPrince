"""Re-classify terrain for all 460 hexes from the one-piece scan using correct geometry.

Usage:
    python _refs/reclassify_terrain.py [hexes.json]

Reads _refs/barbarianprince_onepiecemap-revc.jpg with geometry from src/geometry.py.
Overwrites hexes.json with corrected terrain data.
"""
import math
import json
import os
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from geometry import R, DX, DY, NC, NR, SCAN_X0, SCAN_Y0, centre

SCAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'barbarianprince_onepiecemap-revc.jpg')

# Map key terrain -> short code for quick visual checking
TERRAIN_SHORT = {
    'farmland': 'A',  # Farmland (checkered pattern)
    'countryside': 'C',  # Countryside (green)
    'forest': 'F',  # Forest (dark green trees)
    'mountains': 'M',  # Mountains (purple/white peaks)
    'hills': 'H',  # Hills (brownish)
    'badlands': 'B',  # Badlands (reddish-brown)
    'swamp': 'S',  # Swamp (blueish water)
    'desert': 'D',  # Desert (yellow)
    'water': 'W',  # Water (blue)
    'unknown': '?',
}


def load_hexes(path):
    """Load existing hexes.json to preserve structure, just update terrain."""
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def sample_hex(img, col, row, radius_frac=0.65):
    """Sample interior pixels of a hex, excluding white grid lines and labels."""
    A = np.asarray(img)
    cx, cy = centre(col, row)
    rad = radius_frac * R
    H, W = A.shape[:2]

    x1, x2 = max(0, int(cx - rad)), min(W, int(cx + rad) + 1)
    y1, y2 = max(0, int(cy - rad)), min(H, int(cy + rad) + 1)
    sub = A[y1:y2, x1:x2].astype(np.float32)

    if sub.size == 0:
        return np.zeros((0, 3))

    ys, xs = np.mgrid[y1:y2, x1:x2]
    d = np.hypot(xs - cx, ys - cy)
    mask = d <= rad

    px = sub[mask]
    # Drop white pixels (grid lines, labels)
    keep = px.min(axis=1) < 200
    px = px[keep]
    return px


def classify(px):
    """Classify terrain from sampled pixels.

    Returns (terrain_name, features_dict) for debugging.
    """
    if len(px) < 30:
        return 'unknown', {}

    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    lum = (r + g + b) / 3.0

    # Feature detection thresholds (calibrated from BarbarianPrince map colors)
    water = float(((b > r + 20) & (b > g + 8) & (b > 90)).mean())
    tree = float(((g > r + 5) & (g >= b) & (lum < 145)).mean())
    grass = float(((g > r + 5) & (g > b) & (lum >= 145)).mean())
    yellow = float(((r > g + 15) & (g > b + 10) & (lum > 175)).mean())
    brown = float(((r > g + 15) & (r > b + 20) & (lum <= 175)).mean())
    purple = float(((b > g + 10) & (r > g + 5)).mean())
    grey = float(((abs(r - g) < 25) & (abs(g - b) < 25) & (lum < 200)).mean())
    white = float(((r > 200) & (g > 200) & (b > 200)).mean())
    checkered = float(((r > 140) & (g > 130) & (b < 110) & (r > b + 30)).mean())

    features = {
        'water': round(water, 3),
        'tree': round(tree, 3),
        'grass': round(grass, 3),
        'yellow': round(yellow, 3),
        'brown': round(brown, 3),
        'purple': round(purple, 3),
        'grey': round(grey, 3),
        'white': round(white, 3),
        'checkered': round(checkered, 3),
    }

    # Classification logic (order matters - first match wins)
    if water > 0.25:
        t = 'swamp' if (tree + grass) > 0.20 else 'water'
    elif checkered > 0.15:
        t = 'farmland'
    elif purple > 0.20 or (grey > 0.25 and white > 0.10):
        t = 'mountains'
    elif tree > 0.25:
        t = 'forest'
    elif brown > 0.25:
        t = 'badlands'
    elif yellow > 0.25:
        t = 'desert'
    elif (grass + tree) > 0.35:
        t = 'countryside'
    else:
        t = 'countryside'  # default

    return t, features


def main():
    hexes_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'hexes.json')

    # Load existing hex data to preserve structure
    old_hexes = load_hexes(hexes_path)
    old_terrain = {h['id']: h['terrain'] for h in old_hexes}

    img = Image.open(SCAN).convert('RGB')

    hexes = []
    changed = 0
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            hid = f'{col:02d}{row:02d}'
            px = sample_hex(img, col, row)
            terrain, features = classify(px)

            old_t = old_terrain.get(hid, '?')
            if old_t != terrain:
                changed += 1

            # Find corresponding old entry to preserve other fields
            old_entry = next((h for h in old_hexes if h['id'] == hid), {})
            hexes.append({
                'id': hid,
                'col': col,
                'row': row,
                'terrain': terrain,
                'dist': old_entry.get('dist', 0),
            })

    # Write updated hexes
    with open(hexes_path, 'w', encoding='utf-8') as f:
        json.dump(hexes, f, indent=1)

    from collections import Counter
    counts = Counter(h['terrain'] for h in hexes)
    print(f"Reclassified {len(hexes)} hexes, {changed} changed")
    print("Terrain counts:", dict(counts.most_common()))

    # Print first row for quick visual check
    print("\nRow 1 terrain:")
    row1 = [h['terrain'] for h in hexes if h['row'] == 1]
    print(' | '.join(TERRAIN_SHORT.get(t, t) for t in row1))

    # Print first few hex features for debugging
    print("\nSample hex features:")
    for h in hexes[:6]:
        px = sample_hex(img, h['col'], h['row'])
        _, feats = classify(px)
        print(f"  {h['id']} ({h['terrain']}): {feats}")


if __name__ == '__main__':
    main()
