"""Trace river and road chains from the model data for visual comparison."""
import json, os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
with open(os.path.join(DATA, 'features.json'), encoding='utf-8') as f:
    feats = json.load(f)

def parse(hid):
    return int(hid[:2]), int(hid[2:])

# --- Trace river chains (connected components) ---
from collections import defaultdict
adj_r = defaultdict(set)
for a, b in feats['river_sides']:
    adj_r[a].add(b)
    adj_r[b].add(a)

visited = set()
chains = []
for start in sorted(adj_r):
    if start in visited:
        continue
    chain = []
    q = [start]
    while q:
        n = q.pop()
        if n in visited:
            continue
        visited.add(n)
        chain.append(n)
        for nb in sorted(adj_r[n]):
            if nb not in visited:
                q.append(nb)
    if len(chain) > 1:
        chains.append(sorted(chain))

chains.sort(key=lambda c: (-len(c), c[0]))
print("=== RIVER CHAINS (by connected components) ===")
for i, chain in enumerate(chains):
    if len(chain) >= 4:
        print(f"Chain {i+1} ({len(chain)} hexes): {' -> '.join(chain[:20])}")
        if len(chain) > 20:
            print(f"  ... and {len(chain)-20} more hexes")

# --- Trace road chains ---
adj_rd = defaultdict(set)
for a, b in feats['road_sides']:
    adj_rd[a].add(b)
    adj_rd[b].add(a)

visited = set()
rchains = []
for start in sorted(adj_rd):
    if start in visited:
        continue
    chain = []
    q = [start]
    while q:
        n = q.pop()
        if n in visited:
            continue
        visited.add(n)
        chain.append(n)
        for nb in sorted(adj_rd[n]):
            if nb not in visited:
                q.append(nb)
    if len(chain) > 1:
        rchains.append(sorted(chain))

rchains.sort(key=lambda c: (-len(c), c[0]))
print("\n=== ROAD CHAINS (by connected components) ===")
for i, chain in enumerate(rchains):
    if len(chain) >= 3:
        print(f"Chain {i+1} ({len(chain)} hexes): {' -> '.join(chain[:20])}")
        if len(chain) > 20:
            print(f"  ... and {len(chain)-20} more hexes")
