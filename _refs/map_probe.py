"""Map geometry: how far are the ruins and temples from the start?

Prints, per campaign, the expected travel days from 0101 to the nearest ruin,
from that ruin to the nearest temple, and the best ruin/temple pair.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
rows = []
for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    r, rd = b.nearest('ruins')
    t, td = b.nearest('temple')
    best = None
    for h, p in g.features['places'].items():
        if p['kind'] != 'ruins':
            continue
        tt, ttd = b.nearest('temple', h)
        camp = 70 - 1 - b.travel_days(h).get('0101', 999) - ttd
        if best is None or camp > best[0]:
            best = (camp, h, tt, b.travel_days(h).get('0101', 999), ttd)
    n_ruins = sum(1 for p in g.features['places'].values() if p['kind'] == 'ruins')
    n_temples = sum(1 for p in g.features['places'].values() if p['kind'] == 'temple')
    rows.append((rd, td, best[0], best[3], best[4], n_ruins, n_temples))

def avg(i):
    return sum(r[i] for r in rows) / len(rows)

print(f'{N} campaigns')
print(f'nearest ruin  {avg(0):.1f} days   nearest temple {avg(1):.1f} days')
print(f'best camp days {avg(2):.1f}  (start->ruin {avg(3):.1f}, ruin->temple {avg(4):.1f})')
print(f'ruins per map {avg(5):.1f}  temples per map {avg(6):.1f}')
print('best camp days histogram:', sorted(
    (int(r[2]), sum(1 for x in rows if int(x[2]) == int(r[2]))) for r in set(rows))[:20])
