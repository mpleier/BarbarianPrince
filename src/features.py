"""Board features: roads, river crossings, named places, terrain colours.

Derived from the verified hex grid plus the side/road detection scans, and
cross-checked against the printed map legend and the rule text
(r211 names Huldra Castle 1212, Drogat Castle 0323, Aeravir Castle 1923).

Writes data/features.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
REFS = os.path.join(ROOT, '_refs')

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


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_features():
    hexes = load(os.path.join(REFS, 'hexes.json'))
    links = load(os.path.join(REFS, 'road_links.json'))
    road_hexes = load(os.path.join(REFS, 'roadhexes.json'))

    grid = {h['id']: h for h in hexes}

    road_hexes_clean = {hid: p for hid, p in road_hexes.items() if p > 0.12}

    river_sides = set()
    road_sides = set()
    for key, (blue, road) in links.items():
        a, b = key.split('|')
        pair = tuple(sorted((a, b)))
        if blue > 0.35:
            river_sides.add(pair)
        if road > 0.35:
            road_sides.add(pair)

    # A hex is "on a road" if the drawn road mask covers it and it has a link.
    on_road = {hid for hid in road_hexes_clean if any(
        tuple(sorted((hid, n))) in road_sides for n in grid[hid]['neighbors'].values())}


    features = {
        'terrain_colors': TERRAIN_COLORS,
        'places': {hid: {'name': name, 'kind': kind} for hid, (name, kind) in PLACES.items()},
        'regions': REGION_LABELS,
        'road_hexes': sorted(on_road),
        'river_sides': sorted(tuple(sorted(p)) for p in river_sides),
        'road_sides': sorted(tuple(sorted(p)) for p in road_sides),
    }
    return features


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
    print('places:', len(feats['places']))


if __name__ == '__main__':
    main()
