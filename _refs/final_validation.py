"""
Final validation report for the fixed features.json.

Checks:
1. All river/road edges connect adjacent hexes
2. Report chain connectivity statistics
3. Identify any remaining connectivity gaps for major rivers
4. Compare with backup to show what changed
"""
import json, sys, os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from geometry import neighbours, parse_hex

FEAT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'features.json')
FEAT_BAK = os.path.join(os.path.dirname(__file__), '..', 'data', 'features.json.bak')

# Load current and backup
features = json.load(open(FEAT_PATH, encoding='utf-8'))
features_bak = json.load(open(FEAT_BAK, encoding='utf-8'))

# Check all edges for adjacency
def validate_adjacency(edges, name):
    bad = []
    for e in edges:
        c1, r1 = parse_hex(e[0])
        c2, r2 = parse_hex(e[1])
        nbs = neighbours(c1, r1)
        nb_str = f"{c2:02d}{r2:02d}"  # Zero-padded to match neighbours() output
        if nb_str not in nbs.values():
            bad.append((e[0], e[1]))
    return bad

river_bad = validate_adjacency(features['river_sides'], 'river')
road_bad = validate_adjacency(features['road_sides'], 'road')

# Compare counts
river_curr = len(features['river_sides'])
river_orig = len(features_bak['river_sides'])
road_curr = len(features['road_sides'])
road_orig = len(features_bak['road_sides'])

print("=" * 60)
print("FINAL VALIDATION REPORT")
print("=" * 60)
print(f"\nRiver edges: {river_curr} (was {river_orig}, removed {river_orig - river_curr})")
print(f"Road edges:  {road_curr} (was {road_orig}, removed {road_orig - road_curr})")
print(f"\nInvalid river adjacencies: {len(river_bad)}")
print(f"Invalid road adjacencies:  {len(road_bad)}")

if river_bad:
    print("\nBAD river edges remaining:")
    for a, b in river_bad:
        print(f"  {a}-{b}")
if road_bad:
    print("\nBAD road edges remaining:")
    for a, b in road_bad:
        print(f"  {a}-{b}")

# Count chains
def count_chains(edges):
    adj = defaultdict(set)
    for e in edges:
        adj[e[0]].add(e[1])
        adj[e[1]].add(e[0])
    visited = set()
    chains = []
    for node in adj:
        if node not in visited:
            chain = set()
            stack = [node]
            while stack:
                n = stack.pop()
                if n not in visited:
                    visited.add(n)
                    chain.add(n)
                    stack.extend(adj[n] - visited)
            chains.append(chain)
    return chains

river_chains = count_chains(features['river_sides'])
road_chains = count_chains(features['road_sides'])

print(f"\nRiver chains: {len(river_chains)}")
print(f"  Largest: {len(max(river_chains, key=len))} hexes")
print(f"  Single-edge: {sum(1 for c in river_chains if len(c) == 2)}")

print(f"\nRoad chains: {len(road_chains)}")
print(f"  Largest: {len(max(road_chains, key=len))} hexes")
print(f"  Single-edge: {sum(1 for c in road_chains if len(c) == 2)}")

print("\n" + "=" * 60)
if river_bad or road_bad:
    print("STATUS: INVALID - bad adjacencies remain")
else:
    print("STATUS: VALID - all edges connect adjacent hexes")
print("=" * 60)
