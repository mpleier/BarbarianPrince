"""Board features: roads, river crossings, named places, terrain colours.

Roads and rivers are traced from the board scan itself: the scan is split
into a "river" mask (saturated blue-cyan ink) and a "road" mask (brick-red
ink), and every hex side is then scored by how closely the drawn line runs
along it.  A side is a river/road side only when the ink covers a good part
of the shared edge, which guarantees that both hexes really are adjacent -
the older detector linked pixel blobs and occasionally paired hexes that do
not touch.

Writes data/features.json
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

from geometry import (R, DX, DY, SCAN_X0, SCAN_Y0, neighbours, parse_hex,
                      hex_id, NC, NR)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
REFS = os.path.join(ROOT, '_refs')
SCAN = os.path.join(REFS, 'BPMap.jpg')

# The colour-corrected scan is stored with a wider page (map key on the left).
# Its lattice is the BPMap one shifted by the content box and scaled by about
# 0.4%:  (264 + (x-1)*1.00165, 9 + (y-5)*0.99567).
SCAN_REVC = os.path.join(REFS, 'barbarianprince_onepiecemap-revc.jpg')
CALIB_REVC = (79.5, 343.6, 77.6)

# Terrain -> (fill, outline) colours used by the GUI map.
TERRAIN_COLORS = {
    'farmland': '#dfe9b0',
    'countryside': '#a9d18a',
    'forest': '#2f7d43',
    'hills': '#c3a976',
    'badlands': '#b0655f',
    'mountains': '#c9c9d8',
    'swamp': '#7fb6a8',
    'desert': '#f2d98c',
    'water': '#5b9bd5',
    'unknown': '#d8d8d8',
}

# Named places printed on the board (verified against the scans).
PLACES = {
    '0101': ('Ogon', 'town'),
    '0109': ('Angleae', 'town'),
    '0801': ("Jakor's Keep", 'ruins'),
    '1005': ('Sumry', 'town'),
    '1109': ('Cawther', 'town'),
    '1209': ("Donay's Temple", 'temple'),
    '1212': ('Huldra Castle', 'castle'),
    '1501': ('Weshor', 'town'),
    '1611': ('Hill Tribe camp', 'camp'),
    '1706': ('Temple of Zhor', 'temple'),
    '2018': ('Duffyd Temple', 'temple'),
    '2008': ('Ruins of Pelgar', 'ruins'),
    '0307': ('Dead Plains Ruins', 'ruins'),
    '0611': ("Branwyn's Temple", 'temple'),
    '0921': ('Sulwyth Temple', 'temple'),
    '0420': ('Halowich', 'town'),
    '0423': ('Lower Drogat', 'town'),
    '0323': ('Drogat Castle', 'castle'),
    '1923': ('Aeravir Castle', 'castle'),
    '2004': ('North Pass', 'pass'),
    '1812': ('South Pass', 'pass'),
    '1423': ('Samain Marshes', 'marsh'),
}

PLACE_KINDS = {'town', 'castle', 'temple', 'ruins'}

REGION_LABELS = {
    '0307': 'The Dead Plains',
    '1507': 'Kabir Desert',
    '1411': 'Wredwrock Badlands',
    '1705': 'Mountains of Zhor',
    '1106': 'Misty Mountains',
}

# ------------------------------------------------------------------ tracing
# A river side has river ink along most of its edge; a river merely crossing
# the edge clips it at one point and scores far worse.  The masks are grown
# by a couple of pixels first, because the artwork draws rivers as separate
# blue patches that only connect when the ink is dilated.
RIVER_MAX_MEAN_DIST = 11.0     # px
RIVER_MIN_COVERAGE = 0.45      # fraction of the edge within COVER_DIST
ROAD_MAX_MEAN_DIST = 16.0
ROAD_MIN_COVERAGE = 0.20
COVER_DIST = 12.0

WATER_MIN_AREA = 300           # drop specks (mountain shading, ink noise)
WATER_MAX_WIDTH = 16.0         # px; wider blobs are lakes, not rivers
ROAD_MIN_SPAN = 100.0          # px; hatching strokes are short, roads are long


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _keep_rivers(mask):
    """Keep narrow, ink-sized components; lakes and big washes are dropped."""
    labels, count = ndimage.label(ndimage.binary_dilation(mask, iterations=1),
                                  structure=np.ones((3, 3)))
    if count == 0:
        return mask
    inside = ndimage.distance_transform_edt(labels > 0)
    width = ndimage.maximum(inside, labels, range(1, count + 1))
    areas = ndimage.sum(labels > 0, labels, range(1, count + 1))
    keep = [i + 1 for i, (w, area) in enumerate(zip(width, areas))
            if area >= WATER_MIN_AREA and w <= WATER_MAX_WIDTH]
    return np.isin(labels, keep)


def _keep_roads(mask):
    """Keep elongated components; short hatching strokes are dropped."""
    labels, count = ndimage.label(ndimage.binary_dilation(mask, iterations=1),
                                  structure=np.ones((3, 3)))
    keep = []
    for i, box in enumerate(ndimage.find_objects(labels)):
        if box is None:
            continue
        dy = box[0].stop - box[0].start
        dx = box[1].stop - box[1].start
        if (dx * dx + dy * dy) ** 0.5 >= ROAD_MIN_SPAN:
            keep.append(i + 1)
    return np.isin(labels, keep)


def _masks(img):
    """(river, road) boolean masks for an RGB scan."""
    a = np.asarray(img, dtype=np.float32)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    lum = (r + g + b) / 3.0

    # Rivers are saturated blue-cyan ink; purple/blue mountain shading is
    # rejected by requiring green above red.
    water = (g > r + 2) & (b > g + 8) & (b - r > 25) & (b > 85) & (lum < 215)

    # Roads are red-brown ink; desert stipple and badlands hatching sit close
    # to that colour, so they are separated by shape below.
    road = (r - g > 30) & (r - b > 40) & (g - b > 2) & (r > 100) & (g < 175)

    water = ndimage.binary_dilation(_keep_rivers(water), iterations=2)
    road = ndimage.binary_dilation(_keep_roads(road), iterations=2)
    return water, road


def _sides(calib=None):
    """Every undirected pair of adjacent hexes, with its shared edge.

    ``calib`` is (radius, x0, y0) for the scan being traced; it defaults to
    the geometry module's BPMap calibration.
    """
    radius, x0, y0 = calib or (R, SCAN_X0, SCAN_Y0)

    def point(col, row):
        dy = DY * (row - 1) + (DY / 2 if col % 2 == 0 else 0.0)
        return np.array([x0 + DX * (col - 1), y0 + dy], dtype=float)

    seen = set()
    out = []
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            a = hex_id(col, row)
            ca = point(col, row)
            for nb in neighbours(col, row).values():
                key = tuple(sorted((a, nb)))
                if key in seen:
                    continue
                seen.add(key)
                cb = point(*parse_hex(nb))
                mid = (ca + cb) / 2.0
                along = cb - ca
                along /= np.linalg.norm(along)
                across = np.array([-along[1], along[0]])
                out.append((key, mid - across * radius / 2, mid + across * radius / 2))
    return out


def _profile(dmap, p1, p2, samples=23, along=0.44):
    """(mean distance, coverage) of ink along the edge p1-p2."""
    mid = (p1 + p2) / 2.0
    edge = p2 - p1
    values = []
    for t in np.linspace(-along, along, samples):
        p = mid + edge * t
        x, y = int(round(p[0])), int(round(p[1]))
        if 0 <= y < dmap.shape[0] and 0 <= x < dmap.shape[1]:
            values.append(dmap[y, x])
    if not values:
        return 99.0, 0.0
    ds = np.asarray(values)
    return float(ds.mean()), float((ds <= COVER_DIST).mean())


def detect_sides(scan=SCAN, calib=None):
    """Trace river and road sides from the board scan."""
    img = Image.open(scan).convert('RGB')
    water, road = _masks(img)
    dw = ndimage.distance_transform_edt(~water)
    dr = ndimage.distance_transform_edt(~road)

    rivers, roads = [], []
    for key, p1, p2 in _sides(calib):
        mean, cover = _profile(dw, p1, p2)
        if mean <= RIVER_MAX_MEAN_DIST and cover >= RIVER_MIN_COVERAGE:
            rivers.append(key)
            continue
        mean, cover = _profile(dr, p1, p2)
        if mean <= ROAD_MAX_MEAN_DIST and cover >= ROAD_MIN_COVERAGE:
            roads.append(key)
    return sorted(rivers), sorted(roads)


def build_features():
    river_sides, road_sides = detect_sides()
    road_hexes = sorted({h for pair in road_sides for h in pair})
    return {
        'terrain_colors': TERRAIN_COLORS,
        'places': {hid: {'name': name, 'kind': kind} for hid, (name, kind) in PLACES.items()},
        'regions': REGION_LABELS,
        'road_hexes': road_hexes,
        'river_sides': [list(p) for p in river_sides],
        'road_sides': [list(p) for p in road_sides],
    }


def load_features():
    """Load the pre-built features (building them if the file is missing)."""
    path = os.path.join(DATA, 'features.json')
    if not os.path.exists(path):
        feats = build_features()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(feats, f, indent=1)
        return feats
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    feats = build_features()
    with open(os.path.join(DATA, 'features.json'), 'w', encoding='utf-8') as f:
        json.dump(feats, f, indent=1)
    print('road hexes:', len(feats['road_hexes']))
    print('river sides:', len(feats['river_sides']))
    print('road sides:', len(feats['road_sides']))
    print('places:', len(feats['places']))


if __name__ == '__main__':
    main()
