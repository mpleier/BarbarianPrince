"""Build river chains from the corrected side data and print them in order."""
import json
import sys
from collections import defaultdict

sys.path.insert(0, r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\src')
from geometry import neighbours, parse_hex

LINKS = json.load(open(r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\_refs\road_links_fixed.json',
                       encoding='utf-8'))

rivers = [tuple(sorted(k.split('|'))) for k, v in LINKS.items() if v[0] > 0.35]
roads = [tuple(sorted(k.split('|'))) for k, v in LINKS.items() if v[1] > 0.35]

# adjacency graph whose nodes are hexes, edges are river sides
g = defaultdict(set)
for a, b in rivers:
    g[a].add(b)
    g[b].add(a)

seen = set()
comps = []
for start in g:
    if start in seen:
        continue
    stack = [start]
    comp = set()
    while stack:
        x = stack.pop()
        if x in comp:
            continue
        comp.add(x)
        stack.extend(g[x] - comp)
    comps.append(comp)

print('river hex clusters:', len(comps))
for comp in sorted(comps):
    edges = sorted((a, b) for a, b in rivers if a in comp and b in comp)
    deg = defaultdict(int)
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    ends = sorted(h for h in comp if deg[h] == 1)
    branch = sorted(h for h in comp if deg[h] > 2)
    print(f'  cluster {len(comp)} hexes, {len(edges)} sides, ends={ends}, branch={branch}')
    print('   sides:', ' '.join(f'{a}-{b}' for a, b in edges))
