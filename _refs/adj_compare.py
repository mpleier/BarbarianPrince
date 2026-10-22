"""Fix plan: Compare adjacency between detect_links.py and geometry.py"""
import sys
sys.path.insert(0, r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\src')
from geometry import neighbours as geo_neighbours, parse_hex

def detect_neighbours(c, r):
    """From detect_sides.py / detect_links.py"""
    if c % 2 == 1:
        return [(c, r - 1), (c, r + 1), (c + 1, r), (c + 1, r - 1),
                (c - 1, r), (c - 1, r + 1)]
    return [(c, r - 1), (c, r + 1), (c + 1, r), (c + 1, r + 1),
            (c - 1, r), (c - 1, r - 1)]

def hex_id(c, r):
    return f"{c:02d}{r:02d}"

# Check if the two adjacency functions agree
mismatches = 0
total = 0
for c in range(1, 21):
    for r in range(1, 24):
        geo_set = set(geo_neighbours(c, r).values())
        det_set = set(hex_id(nc, nr) for nc, nr in detect_neighbours(c, r)
                     if 1 <= nc <= 20 and 1 <= nr <= 23)
        total += 1
        if geo_set != det_set:
            mismatches += 1
            if mismatches <= 5:
                print(f"  MISMATCH at ({c},{r}):")
                print(f"    geo:  {sorted(geo_set)}")
                print(f"    det:  {sorted(det_set)}")
                print(f"    only in det: {sorted(det_set - geo_set)}")
                print(f"    only in geo: {sorted(geo_set - det_set)}")

print(f"\nTotal hexes checked: {total}")
print(f"Mismatches: {mismatches}")
if mismatches > 0:
    print("\nThe detect_sides.py adjacency differs from geometry.py!")
    print("This explains the 'BAD' edges - detect_sides.py connected hexes")
    print("that geometry.py considers non-adjacent.")
else:
    print("\nAdjacency functions match perfectly.")

# Check specific BAD edges
print("\n=== Checking BAD edges ===")
bad_edges = [
    ('0709', '0810'), ('0807', '0906'), ('0901', '1002'),
    ('1002', '1101'), ('1101', '1202'), ('1814', '1913'),
]
for a, b in bad_edges:
    c, r = parse_hex(a)
    geo_nbs = set(geo_neighbours(c, r).values())
    det_nbs = set(hex_id(nc, nr) for nc, nr in detect_neighbours(c, r)
                 if 1 <= nc <= 20 and 1 <= nr <= 23)
    in_geo = b in geo_nbs
    in_det = b in det_nbs
    print(f"  {a}→{b}: geo={in_geo}, det={in_det}")
    if in_det and not in_geo:
        print(f"    → detect thinks adjacent, geometry does NOT")
