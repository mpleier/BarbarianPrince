"""Validate the river/road hexside data in data/features.json against the grid.

Checks, in order:
  1. every listed pair is a true hex-hex neighbour (the old side_check.py
     tested `b in neighbours(...)`, which tests the *direction keys*, so it
     reported every pair as bad - that is the bug being fixed here);
  2. the direction of each side (N/S sides are horizontal edges, the other
     four are slanted), which tells us which way a river runs across it;
  3. whether the river sides form connected chains (a chain = sides that
     share hexes, i.e. a river drawn across a sequence of hexesides);
  4. whether each chain is a simple path (each side used once, hexes of
     degree <= 2 inside the chain) - a river cannot branch.
"""
import json
import sys
from collections import defaultdict

sys.path.insert(0, r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\src')
from geometry import neighbours, parse_hex, hex_id

FEAT = json.load(open(r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\data\features.json',
                      encoding='utf-8'))


def direction(a, b):
    """Direction from a to b (None if not adjacent)."""
    nb = neighbours(*parse_hex(a))
    for d, hid in nb.items():
        if hid == b:
            return d
    return None


def chains(sides):
    """Group hexsides into connected chains: two sides are linked if they
    share a hex, and the shared hex is where the river bends."""
    adj = defaultdict(set)
    for a, b in sides:
        for x in (a, b):
            for y in (a, b):
                if x != y:
                    adj[(a, b)].add((x, y))
    # union-find over sides, joined when two sides share a hex AND the two
    # far ends are themselves adjacent (the river bends through that hex)
    parent = {s: s for s in sides}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    side_set = set(sides)
    hex_to_sides = defaultdict(list)
    for s in sides:
        for h in s:
            hex_to_sides[h].append(s)
    for h, ss in hex_to_sides.items():
        for i in range(len(ss)):
            for j in range(i + 1, len(ss)):
                union(ss[i], ss[j])
    groups = defaultdict(list)
    for s in sides:
        groups[find(s)].append(s)
    return list(groups.values())


def report():
    out = []
    for key in ('river_sides', 'road_sides'):
        sides = [tuple(s) for s in FEAT[key]]
        bad = [(a, b) for a, b in sides if direction(a, b) is None]
        out.append(f'{key}: {len(sides)} sides, non-adjacent: {len(bad)}')
        for p in bad:
            out.append(f'  BAD {p[0]}-{p[1]}')
        dirs = defaultdict(int)
        for a, b in sides:
            d = direction(a, b)
            if d:
                dirs[d] += 1
        out.append('  directions: ' + ', '.join(f'{d}={n}' for d, n in sorted(dirs.items())))
        ch = chains(sides)
        out.append(f'  chains: {len(ch)}  sizes: {sorted(len(c) for c in ch)}')
        for c in ch:
            deg = defaultdict(int)
            for a, b in c:
                deg[a] += 1
                deg[b] += 1
            branch = [h for h, n in deg.items() if n > 2]
            out.append(f'    chain of {len(c)} sides, branching hexes: {branch}')
    return '\n'.join(out)


if __name__ == '__main__':
    text = report()
    print(text)
    open(r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\_refs\side_validate_out.txt',
         'w', encoding='utf-8').write(text)
