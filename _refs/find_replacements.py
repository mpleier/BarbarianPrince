"""
Find replacement edges for removed BAD river/road connections.

For each BAD edge A-B that connected non-adjacent hexes, find an intermediate hex
C such that A-C and C-B are both valid adjacent pairs. The river/road detection
found real blue/brown pixels between A and B, so the feature passes through the
gap. The intermediate hex C sits between them on the grid.
"""
import json, sys, os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from geometry import neighbours, parse_hex

FEAT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'features.json')
LINKS_PATH = os.path.join(os.path.dirname(__file__), 'road_links.json')

def find_common_neighbor(hex_a, hex_b):
    """Find hexes that are neighbors of both hex_a and hex_b."""
    c1, r1 = parse_hex(hex_a)
    c2, r2 = parse_hex(hex_b)
    nbs_a = set(neighbours(c1, r1).values())
    nbs_b = set(neighbours(c2, r2).values())
    return nbs_a & nbs_b

# Load corrected features
with open(FEAT_PATH, encoding='utf-8') as f:
    features = json.load(f)

river_sides = [tuple(s) for s in features['river_sides']]
road_sides = [tuple(s) for s in features['road_sides']]
river_set = {tuple(sorted(p)) for p in river_sides}
road_set = {tuple(sorted(p)) for p in road_sides}

# Load original links scores
links = json.load(open(LINKS_PATH, encoding='utf-8'))

# BAD edges that were removed
bad_river = [
    ('0113', '0214'), ('0311', '0412'), ('0404', '0503'), ('0405', '0504'),
    ('0411', '0510'), ('0608', '0707'), ('0709', '0810'), ('0710', '0811'),
    ('0711', '0812'), ('0802', '0901'), ('0807', '0906'), ('0901', '1002'),
    ('0913', '1014'), ('0914', '1015'), ('0915', '1016'), ('1002', '1101'),
    ('1004', '1103'), ('1005', '1104'), ('1006', '1105'), ('1018', '1117'),
    ('1021', '1120'), ('1022', '1121'), ('1023', '1122'), ('1101', '1202'),
    ('1118', '1219'), ('1119', '1220'), ('1203', '1302'), ('1219', '1318'),
    ('1418', '1517'), ('1422', '1521'), ('1423', '1522'), ('1522', '1623'),
    ('1612', '1711'), ('1623', '1722'), ('1722', '1823'), ('1803', '1902'),
    ('1810', '1909'), ('1814', '1913'), ('1815', '1914'),
]

bad_road = [
    ('0104', '0205'), ('0223', '0322'), ('0306', '0407'), ('0911', '1012'),
]

print("=" * 70)
print("RIVER EDGE REPLACEMENT ANALYSIS")
print("=" * 70)

for a, b in bad_river:
    common = find_common_neighbor(a, b)
    # Find the intermediate hex C that would make A-C and C-B valid
    # Check which replacement edges already exist
    replacements = []
    for c in common:
        a_c_exists = tuple(sorted((a, c))) in river_set
        c_b_exists = tuple(sorted((c, b))) in river_set
        
        # Check original link scores
        a_c_score = links.get(f"{min(a,c)}|{max(a,c)}", [0, 0])[0]
        c_b_score = links.get(f"{min(c,b)}|{max(c,b)}", [0, 0])[0]
        
        # Original bad edge score
        orig_score = links.get(f"{min(a,b)}|{max(a,b)}", [0, 0])[0]
        
        replacements.append((c, a_c_exists, c_b_exists, a_c_score, c_b_score, orig_score))
    
    print(f"\nBAD edge: {a}-{b} (original score: {replacements[0][5] if replacements else '?'})")
    if common:
        print(f"  Common neighbors: {sorted(common)}")
        for c, a_c, c_b, a_c_s, c_b_s, _ in sorted(replacements):
            status = "OK" if (a_c and c_b) else ("partial" if (a_c or c_b) else "missing")
            print(f"    via {c}: {a}-{c}={'exists' if a_c else 'NEW '}{c_b_s:.3f}  |  {c}-{b}={'exists' if c_b else 'NEW '}{c_b_s:.3f}  [{status}]")
    else:
        print(f"  NO common neighbors found!")

print("\n" + "=" * 70)
print("ROAD EDGE REPLACEMENT ANALYSIS")
print("=" * 70)

for a, b in bad_road:
    common = find_common_neighbor(a, b)
    replacements = []
    for c in common:
        a_c_exists = tuple(sorted((a, c))) in road_set
        c_b_exists = tuple(sorted((c, b))) in road_set
        a_c_score = links.get(f"{min(a,c)}|{max(a,c)}", [0, 0])[1]
        c_b_score = links.get(f"{min(c,b)}|{max(c,b)}", [0, 0])[1]
        orig_score = links.get(f"{min(a,b)}|{max(a,b)}", [0, 0])[1]
        replacements.append((c, a_c_exists, c_b_exists, a_c_score, c_b_score, orig_score))
    
    print(f"\nBAD road: {a}-{b} (original score: {replacements[0][5] if replacements else '?'})")
    if common:
        print(f"  Common neighbors: {sorted(common)}")
        for c, a_c, c_b, a_c_s, c_b_s, _ in sorted(replacements):
            status = "OK" if (a_c and c_b) else ("partial" if (a_c or c_b) else "missing")
            print(f"    via {c}: {a}-{c}={'exists' if a_c else 'NEW '}{a_c_s:.3f}  |  {c}-{b}={'exists' if c_b else 'NEW '}{c_b_s:.3f}  [{status}]")
    else:
        print(f"  NO common neighbors found!")
