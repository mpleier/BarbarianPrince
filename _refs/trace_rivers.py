"""Trace major river chains to verify connectivity."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from geometry import neighbours, parse_hex
from collections import defaultdict

features = json.load(open('data/features.json', encoding='utf-8'))

# Build adjacency graph for river edges
adj = defaultdict(set)
for e in features['river_sides']:
    adj[e[0]].add(e[1])
    adj[e[1]].add(e[0])

# Build adjacency graph for road edges  
road_adj = defaultdict(set)
for e in features['road_sides']:
    road_adj[e[0]].add(e[1])
    road_adj[e[1]].add(e[0])

# Find connected components
def find_components(adj):
    visited = set()
    components = []
    for node in adj:
        if node not in visited:
            component = set()
            stack = [node]
            while stack:
                n = stack.pop()
                if n not in visited:
                    visited.add(n)
                    component.add(n)
                    stack.extend(adj[n] - visited)
            components.append(component)
    return components

# River components
river_comps = find_components(adj)
print("=== RIVER Chains (sorted by size) ===")
for i, comp in enumerate(sorted(river_comps, key=len, reverse=True)):
    print(f"  Chain {i+1}: {len(comp)} hexes - {sorted(comp)}")

# Road components
road_comps = find_components(road_adj)
print("\n=== ROAD Chains (sorted by size) ===")
for i, comp in enumerate(sorted(road_comps, key=len, reverse=True)):
    print(f"  Chain {i+1}: {len(comp)} hexes - {sorted(comp)}")

# Key hexes to check
print("\n=== Key Hex Status ===")
key_hexes = {
    '0901': 'Tragoth northern',
    '1105': 'Tragoth Sumry',
    '1418': 'Argos',
    '1803': 'Argos southern',
    '1018': 'Nesser River',
    '1212': 'Huldra Castle',
    '0310': 'Nesser town',
    '0615': 'Nesser River',
}
for hex_id, desc in key_hexes.items():
    has_river = hex_id in adj
    has_road = hex_id in road_adj
    print(f"  {hex_id} ({desc}): river={has_river}, road={has_road}")
    if has_river:
        print(f"    River neighbors: {sorted(adj[hex_id])}")
    if has_road:
        print(f"    Road neighbors: {sorted(road_adj[hex_id])}")