"""Road-aware travel analysis: expected days between hexes."""
import sys, heapq, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
from engine import Game

g = Game(seed=1)
m = g.model
roads = g.features['road_sides']
rivers = g.features['river_sides']

LOST = {'Farmland': 10, 'Countryside': 9, 'Forest': 8, 'Hills': 8,
        'Mountains': 7, 'Swamp': 5, 'Desert': 6, 'Cross River': 8,
        'On Road': None, 'Airborne': 12, 'Rafting': None}

def p_lost(terrain):
    thr = LOST.get(terrain)
    if thr is None:
        return 0.0
    # P(2d6 >= thr)
    cnt = sum(1 for a in range(1, 7) for b in range(1, 7) if a + b >= thr)
    return cnt / 36

places = {h: g.place_kind(h) for h in m.grid if g.place_kind(h)}
ruins = sorted(h for h, k in places.items() if k == 'ruins')
temples = sorted(h for h, k in places.items() if k == 'temple')
towns = sorted(h for h, k in places.items() if k in ('town', 'castle'))
print('ruins:', ruins)
print('temples:', temples)
print('towns/castles:', towns)
print('start:', g.hex)

def expected_days(src, dst):
    """Expected number of travel days to step src -> dst (one hex, on foot)."""
    if frozenset((src, dst)) in roads:
        return 1.0
    p = p_lost(m.travel_terrain(src))
    return 1.0 / (1.0 - p)

def dijkstra(start):
    dist = {start: 0.0}
    steps = {start: 0}
    q = [(0.0, 0, start)]
    while q:
        d, s, h = heapq.heappop(q)
        if d > dist.get(h, 1e9):
            continue
        for nb in m.neighbors(h).values():
            nd = d + expected_days(h, nb)
            ns = s + 1
            if nd < dist.get(nb, 1e9) - 1e-9:
                dist[nb] = nd
                steps[nb] = ns
                heapq.heappush(q, (nd, ns, nb))
    return dist, steps

dstart, sstart = dijkstra(g.hex)
print('\nexpected days from start to each ruin:')
for r in ruins:
    print(f'  {r}: {dstart.get(r, float("inf")):.1f} days ({sstart.get(r)} hexes)')
print('\nexpected days from start to each temple:')
for t in temples:
    print(f'  {t}: {dstart.get(t, float("inf")):.1f} days ({sstart.get(t)} hexes)')

print('\nbest ruin->temple pairs (start->ruin->temple):')
pairs = []
for r in ruins:
    dr, sr = dijkstra(r)
    for t in temples:
        pairs.append((dstart[r] + dr[t], r, t, dstart[r], dr[t], sr))
pairs.sort()
for p in pairs[:20]:
    print(f'  {p[1]} -> {p[2]}: total {p[0]:.1f} (to ruin {p[3]:.1f}, to temple {p[4]:.1f})')
