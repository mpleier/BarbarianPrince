"""
Systematically fix BAD edges by finding replacement paths through intermediate hexes.

Strategy:
  - BAD edges with score > 0.35 represent real rivers/roads on the map
  - Each BAD edge A-B is replaced by edges A-C and C-B where C is an intermediate hex
  - We only add edges that exceed the 0.35 threshold OR where the BAD score was high
    (>0.5) and both replacement edges exceed 0.30
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from geometry import neighbours, parse_hex

FEAT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'features.json')
LINKS_PATH = os.path.join(os.path.dirname(__file__), 'road_links.json')

def find_common_neighbor(hex_a, hex_b):
    c1, r1 = parse_hex(hex_a)
    c2, r2 = parse_hex(hex_b)
    nbs_a = set(neighbours(c1, r1).values())
    nbs_b = set(neighbours(c2, r2).values())
    return nbs_a & nbs_b

# Load features and links
with open(FEAT_PATH, encoding='utf-8') as f:
    features = json.load(f)
links = json.load(open(LINKS_PATH, encoding='utf-8'))

river_set = {tuple(sorted(p)) for p in features['river_sides']}
road_set = {tuple(sorted(p)) for p in features['road_sides']}

# Original BAD edges with their detection scores
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

# Build replacement edges
new_river_edges = set()
new_road_edges = set()

print("=== Processing BAD river edges ===")
for a, b in bad_river:
    key = f"{min(a,b)}|{max(a,b)}"
    orig_score = links.get(key, [0, 0])[0]
    common = find_common_neighbor(a, b)
    
    best_replacement = None
    best_score = 0
    
    for c in common:
        # Check if both replacement edges would be above threshold
        a_c_key = f"{min(a,c)}|{max(a,c)}"
        c_b_key = f"{min(c,b)}|{max(c,b)}"
        a_c_score = links.get(a_c_key, [0, 0])[0]
        c_b_score = links.get(c_b_key, [0, 0])[0]
        
        # Check if edges already exist
        a_c_exists = tuple(sorted((a, c))) in river_set
        c_b_exists = tuple(sorted((c, b))) in river_set
        
        if a_c_exists and c_b_exists:
            # Already connected via this intermediate - skip
            best_replacement = ('already_connected', c)
            best_score = 0
            break
        
        # Add replacement edges if scores are high enough
        # Use 0.35 threshold for high-score BAD edges, 0.30 for moderate
        threshold = 0.30 if orig_score > 0.6 else 0.35
        if a_c_score >= threshold and c_b_score >= threshold:
            best_replacement = (c, a_c_score, c_b_score)
            best_score = min(a_c_score, c_b_score)
            break
    
    if best_replacement:
        if best_replacement[0] == 'already_connected':
            print(f"  {a}-{b}: already connected via {best_replacement[1]}")
        else:
            c, a_c_s, c_b_s = best_replacement
            new_river_edges.add(tuple(sorted((a, c))))
            new_river_edges.add(tuple(sorted((c, b))))
            print(f"  {a}-{b}: via {c} (scores {a_c_s:.3f}, {c_b_s:.3f})")
    else:
        print(f"  {a}-{b}: no replacement found (orig={orig_score:.3f})")

print(f"\n=== Processing BAD road edges ===")
for a, b in bad_road:
    key = f"{min(a,b)}|{max(a,b)}"
    orig_score = links.get(key, [0, 0])[1]
    common = find_common_neighbor(a, b)
    
    for c in common:
        a_c_key = f"{min(a,c)}|{max(a,c)}"
        c_b_key = f"{min(c,b)}|{max(c,b)}"
        a_c_score = links.get(a_c_key, [0, 0])[1]
        c_b_score = links.get(c_b_key, [0, 0])[1]
        a_c_exists = tuple(sorted((a, c))) in road_set
        c_b_exists = tuple(sorted((c, b))) in road_set
        
        if a_c_exists and c_b_exists:
            print(f"  {a}-{b}: already connected via {c}")
            break
        threshold = 0.30 if orig_score > 0.6 else 0.35
        if a_c_score >= threshold and c_b_score >= threshold:
            new_road_edges.add(tuple(sorted((a, c))))
            new_road_edges.add(tuple(sorted((c, b))))
            print(f"  {a}-{b}: via {c} (scores {a_c_s:.3f}, {c_b_s:.3f})")
            break
    else:
        print(f"  {a}-{b}: no replacement found (orig={orig_score:.3f})")

# Add new edges to features
print(f"\n=== Adding {len(new_river_edges)} new river edges, {len(new_road_edges)} new road edges ===")
for e in sorted(new_river_edges):
    if e not in river_set:
        river_set.add(e)
        print(f"  River: {e[0]}-{e[1]}")
for e in sorted(new_road_edges):
    if e not in road_set:
        road_set.add(e)
        print(f"  Road:  {e[0]}-{e[1]}")

# Write updated features
features['river_sides'] = sorted([list(p) for p in river_set])
features['road_sides'] = sorted([list(p) for p in road_set])

with open(FEAT_PATH, 'w', encoding='utf-8') as f:
    json.dump(features, f, indent=1)

print(f"\nUpdated features.json:")
print(f"  River sides: {len(river_set)}")
print(f"  Road sides:  {len(road_set)}")
