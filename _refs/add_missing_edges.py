"""
Add missing river/road edges for the major rivers broken by BAD edge removal.

For high-confidence BAD edges (score > 0.5), we add replacement edges with
a lower threshold since the hex grid offset means river pixels don't align
perfectly with corrected hex boundaries.
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from geometry import neighbours, parse_hex

FEAT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'features.json')
LINKS_PATH = os.path.join(os.path.dirname(__file__), 'road_links.json')

def find_best_path(hex_a, hex_b, link_scores, score_key):
    c1, r1 = parse_hex(hex_a)
    c2, r2 = parse_hex(hex_b)
    nbs_a = set(neighbours(c1, r1).values())
    nbs_b = set(neighbours(c2, r2).values())
    common = nbs_a & nbs_b
    best_c = None
    best_min_score = 0
    for c in common:
        a_c_key = f"{min(hex_a,c)}|{max(hex_a,c)}"
        c_b_key = f"{min(c,hex_b)}|{max(c,hex_b)}"
        a_c_score = link_scores.get(a_c_key, [0, 0])[score_key]
        c_b_score = link_scores.get(c_b_key, [0, 0])[score_key]
        min_score = min(a_c_score, c_b_score)
        if min_score > best_min_score:
            best_min_score = min_score
            best_c = (c, a_c_score, c_b_score)
    return best_c

with open(FEAT_PATH, encoding='utf-8') as f:
    features = json.load(f)
links = json.load(open(LINKS_PATH, encoding='utf-8'))

river_set = {tuple(sorted(p)) for p in features['river_sides']}
road_set = {tuple(sorted(p)) for p in features['road_sides']}

print("=== Adding missing river edges ===")
new_river = set()
high_priority_river = [
    ('0901', '1002', 0.847), ('0913', '1014', 0.859), ('1002', '1101', 0.586),
    ('1004', '1103', 0.527), ('1018', '1117', 0.898), ('1023', '1122', 0.740),
    ('1101', '1202', 0.860), ('1418', '1517', 0.602), ('1422', '1521', 0.796),
    ('1423', '1522', 0.771), ('1722', '1823', 0.517), ('1803', '1902', 0.393),
    ('1814', '1913', 0.828), ('1815', '1914', 0.588), ('0914', '1015', 0.599),
    ('0711', '0812', 0.891), ('0802', '0901', 0.626), ('1219', '1318', 0.776),
]
for a, b, score in high_priority_river:
    path = find_best_path(a, b, links, score_key=0)
    if path:
        c, a_c_s, c_b_s = path
        a_c_pair = tuple(sorted((a, c)))
        c_b_pair = tuple(sorted((c, b)))
        threshold = 0.25 if score > 0.7 else 0.30
        needs_a_c = a_c_pair not in river_set and a_c_s >= threshold
        needs_c_b = c_b_pair not in river_set and c_b_s >= threshold
        if needs_a_c or needs_c_b:
            if needs_a_c:
                new_river.add(a_c_pair)
                river_set.add(a_c_pair)
            if needs_c_b:
                new_river.add(c_b_pair)
                river_set.add(c_b_pair)
            print(f"  {a}-{b} via {c}: {a}-{c}({a_c_s:.3f}) {c}-{b}({c_b_s:.3f})")
        else:
            print(f"  {a}-{b}: already connected via {c}")
    else:
        print(f"  {a}-{b}: no path found (score={score})")
