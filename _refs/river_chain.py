import sys, json, math
sys.path.insert(0, r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\src')
from geometry import board_corners, parse_hex

f = json.load(open(r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\data\features.json', encoding='utf-8'))
sides = [tuple(s) for s in f['river_sides']]


def edge(a, b):
    ca = board_corners(*parse_hex(a))
    cb = board_corners(*parse_hex(b))
    pts = [p for p in ca if any(math.hypot(p[0] - q[0], p[1] - q[1]) < 1 for q in cb)]
    return pts


by_vertex = {}
for a, b in sides:
    e = edge(a, b)
    for p in e:
        by_vertex.setdefault((round(p[0]), round(p[1])), []).append((a, b))

# chain: two sides are consecutive if they share exactly one vertex
nxt = {}
for v, lst in by_vertex.items():
    if len(lst) == 2:
        nxt.setdefault(frozenset(lst), []).append(v)

print('total sides', len(sides))
print('sides sharing 2 vertices with other river sides:',
      sum(1 for k, v in nxt.items() if len(v) == 2))

# build chains
seen = set()
chains = []
for s in sides:
    if s in seen:
        continue
    chain = [s]
    seen.add(s)
    cur = s
    while True:
        opts = [t for v in nxt.get(frozenset(cur), []) for t in by_vertex[v] if t != cur and t not in seen]
        if not opts:
            break
        cur = opts[0]
        seen.add(cur)
        chain.append(cur)
    chains.append(chain)

print('chains:', len(chains))
for ch in sorted(chains, key=len, reverse=True):
    hexes = []
    for a, b in ch:
        hexes.append(a)
        hexes.append(b)
    cols = [parse_hex(h)[0] for h in hexes]
    rows = [parse_hex(h)[1] for h in hexes]
    print(len(ch), 'cols', min(cols), max(cols), 'rows', min(rows), max(rows))
    print('  ', ' '.join(f'{a}-{b}' for a, b in ch))
