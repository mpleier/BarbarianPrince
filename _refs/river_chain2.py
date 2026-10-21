import sys, json, math
sys.path.insert(0, r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\src')
from geometry import board_xy, parse_hex, R

f = json.load(open(r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\data\features.json', encoding='utf-8'))
sides = [tuple(s) for s in f['river_sides']]


def shared_edge(a, b):
    ax, ay = board_xy(*parse_hex(a))
    bx, by = board_xy(*parse_hex(b))
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    px, py = -dy / d, dx / d
    return ((mx + px * R / 2, my + py * R / 2), (mx - px * R / 2, my - py * R / 2))


by_vertex = {}
for s in sides:
    for p in shared_edge(*s):
        by_vertex.setdefault((round(p[0]), round(p[1])), []).append(s)

counts = {}
for v, lst in by_vertex.items():
    counts[len(lst)] = counts.get(len(lst), 0) + 1
print('vertex multiplicity:', counts)

adj = {}
for v, lst in by_vertex.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            adj.setdefault(frozenset((lst[i], lst[j])), []).append(v)

print('consecutive pairs:', len(adj))

seen = set()
chains = []
for s in sides:
    if s in seen:
        continue
    chain = [s]
    seen.add(s)
    cur = s
    while True:
        opts = [t for v in adj.get(frozenset(cur), [])
                for t in by_vertex[v] if t != cur and t not in seen]
        if not opts:
            break
        cur = opts[0]
        seen.add(cur)
        chain.append(cur)
    chains.append(chain)

print('chains:', len(chains))
for ch in sorted(chains, key=len, reverse=True):
    hexes = [h for a, b in ch for h in (a, b)]
    cols = [parse_hex(h)[0] for h in hexes]
    rows = [parse_hex(h)[1] for h in hexes]
    print(len(ch), 'cols', min(cols), '-', max(cols), 'rows', min(rows), '-', max(rows))
    print('  ', ' '.join(f'{a}-{b}' for a, b in ch))
