"""Optimal ruin-stopping rule under the real ruin lottery.

V(d, g) = best win chance with d days left, standing at a ruin with g gold.
  go   -> camp(d - travel, g)
  mine -> E[V(d-1, g + Y)]
The crossover gives the gold threshold the bot should use in camping().
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from functools import lru_cache

D = 70
OVERHEAD = 2
GOLD_CAP = 400
RUIN = [(0, 0.9729), (60, 0.0175), (500, 0.0097)]


@lru_cache(maxsize=None)
def camp(d, gold, perm, influence, staff):
    if d <= 0:
        return 0.0
    best = 0.0
    for amount in (1, 10):
        if gold < amount:
            continue
        roll = 2 + min(10, gold) + perm + influence
        win = 1.0 if roll >= 14 else 0.0
        ng = max(0, gold - OVERHEAD - amount)
        ni = influence + (1 if amount == 10 else 0)
        ns = staff or (amount == 10 and influence >= 3)
        best = max(best, win + (1 - win) * camp(d - 1, ng, perm, ni, ns))
    if gold >= OVERHEAD + 5:
        best = max(best, camp(d - 1, max(0, gold - OVERHEAD - 5),
                              perm + 1, influence, staff))
    return best


def solve(travel):
    @lru_cache(maxsize=None)
    def V(d, g):
        if d <= 0:
            return 0.0
        go = camp(max(0, d - travel), g, 0, 0, False)
        if d == 1:
            return go
        mine = sum(p * V(d - 1, min(GOLD_CAP, g + y)) for y, p in RUIN)
        return max(go, mine)

    print(f'travel {travel} days: overall win chance {V(D, 0):.4f}')
    print('  days_left  gold threshold to leave the ruin')
    for d in range(70, 0, -5):
        for g in range(0, GOLD_CAP + 1):
            go = camp(max(0, d - travel), g, 0, 0, False)
            mine = sum(p * V(d - 1, min(GOLD_CAP, g + y)) for y, p in RUIN) if d > 1 else 0
            if go >= mine:
                print(f'    {d:>3}       {g:>4}   (chance {go:.3f})')
                break
        else:
            print(f'    {d:>3}       never leave')


if __name__ == '__main__':
    for t in (4, 6, 8, 10):
        solve(t)
        print()
