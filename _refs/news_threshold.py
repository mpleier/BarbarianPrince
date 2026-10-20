"""Gold threshold at which r209 news-seeking beats the best offering.

For each number of camp days, find the smallest gold where the camp DP prefers
'news' over any offering amount.  Below that the 5-gold bribe and the 6/36
chance of losing half the wealth outweigh the 2/36 permanent +1.
"""
import sys, functools, collections
sys.stdout.reconfigure(encoding='utf-8')

DIST2 = collections.Counter(a + b for a in range(1, 7) for b in range(1, 7))
OVERHEAD = 3
CAP = 600


@functools.lru_cache(maxsize=None)
def camp(d, gold, perm, infl, omen):
    if d <= 0 or gold <= 0:
        return 0.0
    best = camp(d - 1, max(0, gold - OVERHEAD), perm, 0, 0)
    for amt in (1, 5, 10, 20, 50):
        if amt > gold:
            continue
        bonus = perm + infl + omen + (1 if amt >= 10 else 0)
        ev = 0.0
        for s, c in DIST2.items():
            t = s + bonus
            p = c / 36
            ng = max(0, gold - amt - OVERHEAD)
            if t >= 14:
                ev += p
            elif t == 7:
                ev += p * camp(d - 1, ng, perm, 0, 1)
            elif t in (12, 13):
                ev += p * max(camp(d - 1, ng, perm, 3, 0),
                              camp(d - 1, ng, perm, 0, 0))
            else:
                ev += p * camp(d - 1, ng, perm, 0, 0)
        if ev > best:
            best = ev
    if gold >= 5:
        ev = 0.0
        for s, c in DIST2.items():
            t = s + 1
            p = c / 36
            ng = max(0, gold - 5 - OVERHEAD)
            if t == 3:
                ng = min(CAP, ng + 50)
            elif t == 8:
                ng //= 2
            ev += p * camp(d - 1, ng, 1 if t == 4 else perm, 0, 0)
        if ev > best:
            best = ev
    return best


print('camp days -> gold needed before seeking news is optimal')
for d in range(3, 41):
    def offer_ev(g):
        best = 0.0
        for a in (1, 5, 10, 20, 50):
            if a > g:
                continue
            bonus = 1 if a >= 10 else 0
            ev = 0.0
            for s, c in DIST2.items():
                t = s + bonus
                p = c / 36
                ng = max(0, g - a - OVERHEAD)
                if t >= 14:
                    ev += p
                elif t == 7:
                    ev += p * camp(d - 1, ng, 0, 0, 1)
                elif t in (12, 13):
                    ev += p * max(camp(d - 1, ng, 0, 3, 0), camp(d - 1, ng, 0, 0, 0))
                else:
                    ev += p * camp(d - 1, ng, 0, 0, 0)
            best = max(best, ev)
        return best

    def news_ev(g):
        ev = 0.0
        for s, c in DIST2.items():
            t = s + 1
            p = c / 36
            ng = max(0, g - 5 - OVERHEAD)
            if t == 3:
                ng = min(CAP, ng + 50)
            elif t == 8:
                ng //= 2
            ev += p * camp(d - 1, ng, 1 if t == 4 else 0, 0, 0)
        return ev

    lo = next((g for g in range(5, CAP + 1) if news_ev(g) > offer_ev(g)), None)
    print(f'  {d:>3} days: gold >= {lo}')
