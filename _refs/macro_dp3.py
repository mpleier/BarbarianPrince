"""Macro DP with the real ruin lottery.

Ruin searching is not a steady income: measured over 20k searches it pays
0 gold 97.3% of the time, 60 gold 1.75%, and 500 gold 0.97%. The macro plan
therefore has to be evaluated as a distribution, not a mean.

For every ruin length R the gold distribution is convolved and each outcome is
scored with the camp DP from camp_policy.py.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from functools import lru_cache
from collections import Counter

D = 70
OVERHEAD = 2
GOLD_CAP = 400
RUIN = [(0, 0.9729), (60, 0.0175), (500, 0.0097)]


@lru_cache(maxsize=None)
def camp(d, gold, perm, influence, staff):
    """Best win probability with d camp days left at the temple."""
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
        ng = max(0, gold - OVERHEAD - 5)
        best = max(best, camp(d - 1, ng, perm + 1, influence, staff))
    return best


@lru_cache(maxsize=None)
def ruin_dist(r):
    """Distribution of gold after r ruin searches (capped at GOLD_CAP)."""
    if r == 0:
        return {0: 1.0}
    out = Counter()
    prev = ruin_dist(r - 1)
    for g, p in prev.items():
        for y, q in RUIN:
            out[min(GOLD_CAP, g + y)] += p * q
    return dict(out)


def plan():
    best = []
    for t in (4, 6, 8, 10):
        for r in range(0, D - t + 1):
            dist = ruin_dist(r)
            c = D - r - t
            ev = sum(p * camp(c, g, 0, 0, False) for g, p in dist.items())
            best.append((ev, r, t, c))
    best.sort(reverse=True)
    for ev, r, t, c in best[:12]:
        print(f'EV {ev:.4f}  ruin {r:>2}  travel {t:>2}  camp {c:>2}')
    return best


if __name__ == '__main__':
    plan()
    print('\nwin probability by camp days, gold 0/50/100/200/500:')
    for d in (5, 10, 15, 20, 25, 30, 35, 40):
        row = [camp(d, g, 0, 0, False) for g in (0, 50, 100, 200, 500)]
        print(f'  camp {d:>2}: ' + '  '.join(f'{x:.3f}' for x in row))
