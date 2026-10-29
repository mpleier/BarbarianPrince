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

from geometry import (R, RX, RY, DX, DY, SCAN_X0, SCAN_Y0, neighbours, parse_hex,
                      hex_id, NC, NR)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
REFS = os.path.join(ROOT, '_refs')
SCAN = os.path.join(REFS, 'BPMap_rectified.jpg')

# The colour-corrected scan is stored with a wider page (map key on the left)
# and still carries the photograph's keystone, so it keeps its own lattice:
# the unrectified BPMap frame shifted by the content box and scaled by ~0.4%.
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

# A faint side that would join two traced pieces is accepted at these weaker
# scores; a side with no neighbour at all has to be at least this strong.
RIVER_FILL_MEAN = 16.0
RIVER_FILL_COVERAGE = 0.25
RIVER_KEEP_MEAN = 6.0
ROAD_FILL_MEAN = 24.0
ROAD_FILL_COVERAGE = 0.12
ROAD_KEEP_MEAN = 8.0

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
    """(river, river_loose, road) boolean masks for an RGB scan.

    ``river`` requires green well above red: river ink is cyan (g-r ~ 50)
    while the blue-lavender shading that outlines mountain ridges is not
    (g-r ~ 5), so the strict mask keeps ridges out.  ``river_loose`` keeps the
    pale fills of the wide river stretches and is only used to bridge gaps.
    """
    a = np.asarray(img, dtype=np.float32)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    lum = (r + g + b) / 3.0

    base = (g > r + 2) & (b > g + 8) & (b - r > 25) & (b > 85) & (lum < 215)
    strict = base & (g - r >= 25)

    # Roads are red-brown ink; desert stipple and badlands hatching sit close
    # to that colour, so they are separated by shape below.
    road = (r - g > 30) & (r - b > 40) & (g - b > 2) & (r > 100) & (g < 175)

    water = ndimage.binary_dilation(_keep_rivers(strict), iterations=2)
    loose = ndimage.binary_dilation(_keep_rivers(base), iterations=2)
    road = ndimage.binary_dilation(_keep_roads(road), iterations=2)
    return water, loose, road


def _hex_point(col, row, calib=None):
    """Centre of a hex in the frame of the scan being traced."""
    _radius, x0, y0 = calib or (R, SCAN_X0, SCAN_Y0)
    dy = DY * (row - 1) + (DY / 2 if col % 2 == 0 else 0.0)
    return np.array([x0 + DX * (col - 1), y0 + dy], dtype=float)


def _sides(calib=None):
    """Every undirected pair of adjacent hexes, with its shared edge.

    ``calib`` is (radius, x0, y0) for the scan being traced; it defaults to
    the geometry module's BPMap calibration.
    """
    radius, _x0, _y0 = calib or (R, SCAN_X0, SCAN_Y0)
    # the board is slightly taller than wide, so an edge is about this long
    edge_len = radius * (1 + RY / RX) / 2 if calib is None else radius

    def point(col, row):
        return _hex_point(col, row, calib)

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
                out.append((key, mid - across * edge_len / 2,
                            mid + across * edge_len / 2))
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


def _side_adjacency(sides):
    """Map each side to the sides that share a vertex with it.

    Two sides of the same hex touch when their outer hexes are neighbours
    (consecutive edges of the hexagon).
    """
    index = set(sides)
    graph = {s: set() for s in index}
    for (a, b) in index:
        for h, other in ((a, b), (b, a)):
            for nb in neighbours(*parse_hex(h)).values():
                if nb == other:
                    continue
                pair = tuple(sorted((h, nb)))
                if pair in index:
                    graph[(a, b)].add(pair)
    return graph


def _components(selected, graph):
    """Label the connected pieces of the selected side set."""
    label = {}
    current = 0
    for start in selected:
        if start in label:
            continue
        current += 1
        stack = [start]
        label[start] = current
        while stack:
            cur = stack.pop()
            for nb in graph[cur]:
                if nb in selected and nb not in label:
                    label[nb] = current
                    stack.append(nb)
    return label


def _fill_gaps(scores, selected, graph, max_mean, min_cover, passes=3):
    """Add weakly-scored sides that join two already-traced pieces.

    Rivers and roads run across hex boundaries; where the ink is faint the
    strict pass leaves a one-side hole.  A hole that would fuse two separate
    pieces is filled when the ink is merely plausible rather than strong; a
    hole that reaches the edge of the board is filled too, because that is
    where a river or road is allowed to start or stop.
    """
    for _ in range(passes):
        label = _components(selected, graph)
        added = False
        for side, (mean, cover) in scores.items():
            if side in selected or mean > max_mean or cover < min_cover:
                continue
            touching = {label[nb] for nb in graph[side] if nb in label}
            if len(touching) >= 2 or (touching and _on_board_edge(side)):
                selected.add(side)
                added = True
        if not added:
            break
    return selected


def _on_board_edge(side):
    for h in side:
        col, row = parse_hex(h)
        if col in (1, NC) or row in (1, NR):
            return True
    return False


def _prune_isolated(selected, graph, scores, keep_mean):
    """Drop sides with no neighbour side unless the ink is very strong."""
    changed = True
    while changed:
        changed = False
        for side in sorted(selected):
            if graph[side] & selected:
                continue
            if scores[side][0] > keep_mean:
                selected.discard(side)
                changed = True
    return selected


def _terrain():
    """Hex terrain from _refs/hexes.json (empty when it is missing)."""
    path = os.path.join(REFS, 'hexes.json')
    if not os.path.exists(path):
        return {}
    return {h['id']: h['terrain'] for h in load(path)}


def _veto_impossible(sides, scores, terrain):
    """Drop sides the board cannot show as a river crossing.

    Two water hexes share a lake shore, not a river, and a faint line between
    two mountain hexes is usually ridge shading rather than water.
    """
    out = set()
    for side in sides:
        ta = terrain.get(side[0])
        tb = terrain.get(side[1])
        if ta == tb == 'water':
            continue
        if ta == tb == 'mountains' and scores[side][0] > RIVER_KEEP_MEAN:
            continue
        out.add(side)
    return out


def detect_sides(scan=SCAN, calib=None):
    """Trace river and road sides from the board scan."""
    img = Image.open(scan).convert('RGB')
    water, loose, road = _masks(img)
    dw = ndimage.distance_transform_edt(~water)
    dl = ndimage.distance_transform_edt(~loose)
    dr = ndimage.distance_transform_edt(~road)

    sides = _sides(calib)
    graph = _side_adjacency([key for key, _, _ in sides])

    river_scores = {}          # strict ink, decides what is a river
    river_bridge = {}          # loose ink, only used to close gaps
    road_scores = {}
    rivers, roads = set(), set()
    for key, p1, p2 in sides:
        river_scores[key] = _profile(dw, p1, p2)
        river_bridge[key] = _profile(dl, p1, p2)
        road_scores[key] = _profile(dr, p1, p2)
        if (river_scores[key][0] <= RIVER_MAX_MEAN_DIST
                and river_scores[key][1] >= RIVER_MIN_COVERAGE):
            rivers.add(key)
        elif (road_scores[key][0] <= ROAD_MAX_MEAN_DIST
                and road_scores[key][1] >= ROAD_MIN_COVERAGE):
            roads.add(key)

    rivers = _fill_gaps(river_bridge, rivers, graph,
                        RIVER_FILL_MEAN, RIVER_FILL_COVERAGE)
    rivers = _veto_impossible(rivers, river_scores, _terrain())
    rivers = _prune_isolated(rivers, graph, river_scores, RIVER_KEEP_MEAN)
    roads = _fill_gaps(road_scores, roads, graph,
                       ROAD_FILL_MEAN, ROAD_FILL_COVERAGE)
    roads = _prune_isolated(roads, graph, road_scores, ROAD_KEEP_MEAN)
    roads -= rivers                       # a side is one feature or the other
    return sorted(rivers), sorted(roads)


def _road_hexes(road_sides, scan=SCAN, calib=None):
    """Hexes a road passes through, including stretches drawn inside a hex.

    Side tracing only sees roads that follow an edge; the board also draws
    roads across hex interiors, so a hex counts as on-road when road ink
    covers a fair share of its middle as well.
    """
    img = Image.open(scan).convert('RGB')
    _water, _loose, road = _masks(img)
    out = {h for pair in road_sides for h in pair}
    radius = (calib or (R, SCAN_X0, SCAN_Y0))[0]
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            cx, cy = _hex_point(col, row, calib)
            hits = 0
            total = 0
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    if dx * dx + dy * dy > 9:
                        continue
                    x = int(round(cx + dx * radius / 4.0))
                    y = int(round(cy + dy * radius / 4.0))
                    if 0 <= y < road.shape[0] and 0 <= x < road.shape[1]:
                        hits += int(road[y, x])
                        total += 1
            if total and hits / total >= 0.10:
                out.add(hex_id(col, row))
    return sorted(out)


def _river_components(river_sides):
    """Connected river chains as lists of hexes."""
    adj = {}
    for a, b in river_sides:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen = set()
    components = []
    for start in sorted(adj):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        chain = []
        while stack:
            h = stack.pop()
            chain.append(h)
            for nb in adj[h]:
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        components.append(chain)
    return components


def _river_flow(river_sides):
    """Downstream hex for every river side.

    Raft travel is three hexsides a day downriver but only two upriver (r213),
    so each side needs a direction.  The traces carry no names, but the booklet
    names the flows that matter:

      * the Tragoth runs east to west along the top of the board,
      * the Largos leaves the marsh toward the north-east off the map,
      * the Nesser (and the rest of the southern network) runs north to south.

    So the northern staircase (both hexes in rows 1-3) drains west, the separate
    eastern block drains north-east, and everything else drains south.

    The Dienstal Branch is the exception the booklet calls out: it "feeds into
    the Nesser, flowing from the marsh into the Nesser", i.e. it runs *against*
    the southern flow.  The map shows it leaving the lake at 1617, passing
    1517-1518-1417-1418 and joining the Greater Nesser at 1318, so its sides are
    oriented toward that junction.
    """
    components = _river_components(river_sides)
    largos = set()
    for chain in components:
        cols = {int(h[:2]) for h in chain}
        rows = {int(h[2:]) for h in chain}
        if min(cols) >= 15 and min(rows) >= 10 and max(rows) <= 17:
            largos.update(chain)          # the eastern block: the Largos

    dienstal = {'1517', '1518', '1417', '1418'}
    dienstal_mouth = '1318'               # where the branch meets the Nesser

    def distance_to_mouth(hex_id):
        return (abs(int(hex_id[:2]) - int(dienstal_mouth[:2]))
                + abs(int(hex_id[2:]) - int(dienstal_mouth[2:])))

    flow = {}
    for a, b in river_sides:
        ca, ra = int(a[:2]), int(a[2:])
        cb, rb = int(b[:2]), int(b[2:])
        if a in dienstal and b in dienstal:
            # r213: from the marsh into the Nesser
            downstream = min((a, b), key=distance_to_mouth)
        elif a in largos and b in largos:
            # r213: out of the marsh, to the north-east
            downstream = b if (cb, -rb) > (ca, -ra) else a
        elif max(ra, rb) <= 3:
            # r213: the Tragoth runs east to west
            downstream = b if cb < ca else a
        elif rb != ra:
            # the Nesser and the southern network run north to south
            downstream = b if rb > ra else a
        else:
            downstream = min(a, b)        # same row: east -> west
        flow[f'{a}|{b}'] = downstream
        flow[f'{b}|{a}'] = downstream
    return flow


def build_features():
    river_sides, road_sides = detect_sides()
    road_hexes = _road_hexes(road_sides)
    return {
        'terrain_colors': TERRAIN_COLORS,
        'places': {hid: {'name': name, 'kind': kind} for hid, (name, kind) in PLACES.items()},
        'regions': REGION_LABELS,
        'road_hexes': road_hexes,
        'river_sides': [list(p) for p in river_sides],
        'river_flow': _river_flow(river_sides),
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
