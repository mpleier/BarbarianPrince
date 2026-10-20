"""Where are the towns relative to the ruin->temple route?

The horse dealer only appears in a town or castle (r210), so the detour is only
worth it if one sits near the path.  This measures, for every campaign, the
shortest detour from the planned ruin to the nearest town and back to the
temple, and the expected days a mount would save.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot, TOTAL_DAYS


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    plan = b.plan()
    if not plan:
        return None
    _, ruin, temple = plan
    d_ruin = b.travel_days(ruin)
    d_temple = b.travel_days(temple)
    direct = d_temple.get(ruin, 999.0)
    best = None
    for h, p in g.features['places'].items():
        if p['kind'] not in ('town', 'castle'):
            continue
        a = d_ruin.get(h, 999.0)      # ruin -> town (reverse of town -> ruin)
        c = d_temple.get(h, 999.0)    # town -> temple
        cost = a + 1.0 + 0.861 * c
        if best is None or cost < best[1]:
            best = (h, cost, a, c)
    return direct, best


def main(n):
    saved = []
    detours = 0
    for s in range(1, n + 1):
        r = run(s)
        if not r:
            continue
        direct, best = r
        if best:
            gain = direct - best[1]
            saved.append(gain)
            if gain > 0:
                detours += 1
    print(f'{n} campaigns')
    print(f'  mean direct ruin->temple days {sum(d for d in [0])/n if False else 0:.1f}')
    print(f'  towns within reach: {len(saved)}')
    print(f'  detour worth taking (gain > 0): {detours} ({detours/len(saved):.1%})')
    print(f'  mean expected days saved if taken: {sum(saved)/len(saved):.2f}')
    print(f'  best-case gain: {max(saved):.2f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
