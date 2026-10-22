"""
Fix BAD (non-adjacent) edges in features.json river_sides and road_sides.

ROOT CAUSE: detect_links.py and detect_sides.py generated edges using their own
center/neighbor logic that produced some edges between non-adjacent hexes in the
canonical geometry.py grid.  These edges connect hexes that are visually adjacent
on the map but separated by a column+row offset of (1,1) or (1,2) in the offset
hex coordinate system.

This script:
  1. Loads features.json
  2. Validates every river/road side edge using geometry.py's neighbour function
  3. Removes edges that connect non-adjacent hexes
  4. Reports removed edges for manual review
  5. Saves corrected features.json
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from geometry import neighbours, parse_hex

# --- Configuration ---
FEAT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'features.json')
BACKUP_PATH = FEAT_PATH + '.bak'

def is_adjacent(hex_a, hex_b):
    """Check if two hex IDs are adjacent according to geometry.py."""
    c1, r1 = parse_hex(hex_a)
    c2, r2 = parse_hex(hex_b)
    nbs = neighbours(c1, r1)
    return hex_b in nbs.values()

def fix_features():
    if not os.path.exists(FEAT_PATH):
        print(f"ERROR: {FEAT_PATH} not found")
        return
    
    # Load and backup
    with open(FEAT_PATH, encoding='utf-8') as f:
        features = json.load(f)
    
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=1)
    print(f"Backup saved to {BACKUP_PATH}")
    
    # Process river sides
    old_river = [tuple(s) for s in features['river_sides']]
    good_river = []
    bad_river = []
    for a, b in old_river:
        if is_adjacent(a, b):
            good_river.append((a, b))
        else:
            bad_river.append((a, b))
    
    # Process road sides
    old_road = [tuple(s) for s in features['road_sides']]
    good_road = []
    bad_road = []
    for a, b in old_road:
        if is_adjacent(a, b):
            good_road.append((a, b))
        else:
            bad_road.append((a, b))
    
    # Report
    print(f"\n=== River sides ===")
    print(f"  Before: {len(old_river)} edges")
    print(f"  Valid:  {len(good_river)} edges")
    print(f"  Bad:    {len(bad_river)} edges removed")
    print(f"  Bad river edges:")
    for a, b in bad_river:
        c1, r1 = parse_hex(a)
        c2, r2 = parse_hex(b)
        print(f"    {a}-{b}  (Δc={c2-c1:+d}, Δr={r2-r1:+d})")
    
    print(f"\n=== Road sides ===")
    print(f"  Before: {len(old_road)} edges")
    print(f"  Valid:  {len(good_road)} edges")
    print(f"  Bad:    {len(bad_road)} edges removed")
    print(f"  Bad road edges:")
    for a, b in bad_road:
        c1, r1 = parse_hex(a)
        c2, r2 = parse_hex(b)
        print(f"    {a}-{b}  (Δc={c2-c1:+d}, Δr={r2-r1:+d})")
    
    # Write corrected features
    features['river_sides'] = sorted([list(p) for p in good_river])
    features['road_sides'] = sorted([list(p) for p in good_road])
    
    with open(FEAT_PATH, 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=1)
    print(f"\nCorrected features.json saved to {FEAT_PATH}")
    print(f"  River sides: {len(good_river)}")
    print(f"  Road sides:  {len(good_road)}")

if __name__ == '__main__':
    fix_features()
