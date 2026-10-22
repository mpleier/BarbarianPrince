"""Check Huldra Castle road connectivity and nearby road scores."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from geometry import neighbours, parse_hex

links = json.load(open('_refs/road_links.json', encoding='utf-8'))
features = json.load(open('data/features.json', encoding='utf-8'))

print("=== Huldra Castle (1212) Road Connectivity ===")
nbs = neighbours(12, 12)
print(f"Neighbors of 1212: {sorted(nbs.values())}")
print("\nRoad link scores from 1212 to neighbors:")
for nb in sorted(nbs.values()):
    key = f"1212|{nb}" if nb > "1212" else f"{nb}|1212"
    score = links.get(key, [0, 0])[1]
    print(f"  1212-{nb}: {score:.3f}")

print("\nRiver link scores from 1212 to neighbors:")
for nb in sorted(nbs.values()):
    key = f"1212|{nb}" if nb > "1212" else f"{nb}|1212"
    score = links.get(key, [0, 0])[0]
    print(f"  1212-{nb}: {score:.3f}")

print("\n=== Nearby road edges ===")
nearby_hexes = set(nbs.values()) | {"1212"}
for e in features['road_sides']:
    if e[0] in nearby_hexes or e[1] in nearby_hexes:
        print(f"  {e[0]}-{e[1]}")

print("\n=== Nesser River area (hexes 1018-1023, 1117-1122) ===")
nesser_hexes = [f"{c}{r}" for c in [10, 11] for r in range(17, 24)]
for h in nesser_hexes:
    c, r = parse_hex(h)
    nbs = set(neighbours(c, r).values())
    for nb in sorted(nbs):
        key = f"{min(h,nb)}|{max(h,nb)}"
        r_score = links.get(key, [0, 0])[0]
        if r_score >= 0.25:
            print(f"  {h}-{nb}: river={r_score:.3f}")