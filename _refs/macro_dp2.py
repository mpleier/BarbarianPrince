"""Macro strategy DP over the map: (days left, hex, gold, permanent omen).

Models travel (with the r205 'getting lost' penalty), ruin searching and temple
offerings, so the optimal ruin/temple pair and the mining/camping split can be
read off directly.
"""
import sys, functools, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
from engine import Game

DIST2 = collections.Counter(a + b for a in range(1, 7) for b in range(1, 7))
P2 = {s: c / 36 for s, c in DIST2.items()}

LOST = {'Farmland': 10, 'Countryside': 9, 'Forest': 8, 'Hills': 8,
        'Mountains': 7, 'Swamp': 5, 'Desert': 6, 'Cross River': 8,
        'On Road': None, 'Airborne': 12, 'Rafting': None}

def p_lost(terrain):
    thr = LOST.get(terrain)
    if thr is None:
        return 0.0
    return sum(c for s, c in DIST2.items() if s >= thr) / 36

# Empirical ruin payout (400 campaigns, _refs/measure.py)
RUIN = [(0, 0.971), (50, 0.020), (500, 0.009)]

GMAX = 400
STEP = 10
NB = GMAX // STEP + 1

g = Game(seed=1)
model = g.model
roads = g.features['road_sides']
kind = {h: g.place_kind(h) for h in model.grid}
terr = {h: model.travel_terrain(h) for h in model.grid}
nbrs = {h: list(model.neighbors(h).values()) for h in model.grid}


@functools.lru_cache(maxsize=None)
def camp(d, gold, perm, infl, omen):
    if d <= 0 or gold < 1:
        return 0.0
    best = 0.0
    for amt in (1, 5, 10, 20, 50):
        if amt > gold:
            continue
        bonus = perm + infl + omen + (1 if amt >= 10 else 0)
        ev = 0.0
        for s, c in DIST2.items():
            t = s + bonus
            p = c / 36
            if t >= 14:
                ev += p
            elif t == 7:
                ev += p * camp(d - 1, gold - amt, perm, 0, 1)
            elif t in (12, 13):
                ev += p * max(camp(d - 1, gold - amt, perm, 3, 0),
                              camp(d - 1, gold - amt, perm, 0, 0))
            else:
                ev += p * camp(d - 1, gold - amt, perm, 0, 0)
        if ev > best:
            best = ev
    return best


@functools.lru_cache(maxsize=None)
def ruin_ev(d, h, gold, perm):
    ev = 0.0
    for p, prob in RUIN:
        ev += prob * V(d - 1, h, min(GMAX, gold + p), perm)
    return ev


@functools.lru_cache(maxsize=None)
def V(d, h, gold, perm):
    if d <= 0:
        return 0.0
    stay = V(d - 1, h, gold, perm)
    best = stay
    if kind[h] == 'temple':
        best = max(best, camp(d, gold, perm, 0, 0))
    if kind[h] == 'ruins':
        best = max(best, ruin_ev(d, h, gold, perm))
    for nb in nbrs[h]:
        pl = 0.0 if frozenset((h, nb)) in roads else p_lost(terr[h])
        ev = (1 - pl) * V(d - 1, nb, gold, perm) + pl * stay
        if ev > best:
            best = ev
    return best


start = g.hex
print('optimal win probability from the start:')
for perm in (0, 1):
    print(f'  perm={perm}: {V(70, start, 0, perm):.4f}')

print('\nbest ruin to farm / temple to camp (from start, 70 days):')
ruins = [h for h in model.grid if kind[h] == 'ruins']
temples = [h for h in model.grid if kind[h] == 'temple']
for r in ruins:
    print(f'  ruin {r}: {V(70, r, 0, 0):.4f}')
for t in temples:
    print(f'  temple {t}: {V(70, t, 0, 0):.4f}')

print('\npolicy trace from the start (gold rounded to 10):')
d, h, gold, perm = 70, start, 0, 0
seen = collections.Counter()
for _ in range(70):
    if d <= 0:
        break
    opts = [('stay', V(d - 1, h, gold, perm))]
    if kind[h] == 'temple':
        opts.append(('camp', camp(d, gold, perm, 0, 0)))
    if kind[h] == 'ruins':
        opts.append(('ruins', ruin_ev(d, h, gold, perm)))
    for nb in nbrs[h]:
        pl = 0.0 if frozenset((h, nb)) in roads else p_lost(terr[h])
        ev = (1 - pl) * V(d - 1, nb, gold, perm) + pl * V(d - 1, h, gold, perm)
        opts.append((f'move {nb}', ev))
    opts.sort(key=lambda x: -x[1])
    act, val = opts[0]
    seen[act if act in ('ruins', 'camp', 'stay') else 'move'] += 1
    print(f'  days_left={d:>2} hex={h} gold={gold:>3} -> {act} ({val:.4f})')
    if act == 'ruins':
        gold = min(GMAX, gold + 6)
    elif act == 'camp':
        gold = max(0, gold - 1)
    elif act.startswith('move'):
        h = act.split()[1]
    d -= 1
print('action counts:', seen)
