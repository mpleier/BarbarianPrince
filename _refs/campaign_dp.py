"""Full campaign DP: how many ruin days, then what to do at the temple.

States are (days left at the temple, gold, permanent news omen, influence,
omen).  Actions are: end the day, offer 1/5/10/20/50 gold, or seek news (r209)
for 5 gold.  A temple day always costs OVERHEAD gold in food and lodging.

The ruin phase is a simple linear gold source (RUIN_YIELD gold per day), so
the outer loop just tries every split of the 70 days between mining and
camping and reports which one maximises the win probability.
"""
import sys, functools, collections
sys.stdout.reconfigure(encoding='utf-8')

DIST2 = collections.Counter(a + b for a in range(1, 7) for b in range(1, 7))
OVERHEAD = 3
RUIN_YIELD = 5.6
TOTAL_DAYS = 70
CAP = 600


@functools.lru_cache(maxsize=None)
def camp(d, gold, perm, infl, omen):
    """Best win probability with d temple days left."""
    if d <= 0 or gold <= 0:
        return 0.0
    best = 0.0
    # end the day (no offering)
    best = max(best, camp(d - 1, max(0, gold - OVERHEAD), perm, 0, 0))
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
    # r209: seek news.  5 gold buys a +1 on the 2d6 (the Prince's wit is 4).
    if gold >= 5:
        ev = 0.0
        for s, c in DIST2.items():
            t = s + 1
            p = c / 36
            ng = max(0, gold - 5 - OVERHEAD)
            if t == 3:
                ng = min(CAP, ng + 50)
            elif t == 4:
                ev += p * (1 - camp(d - 1, ng, 1, 0, 0)) * 0  # handled below
            elif t == 8:
                ng //= 2
            ev += p * camp(d - 1, ng, 1 if t == 4 else perm, 0, 0)
        if ev > best:
            best = ev
    return best


def action(d, gold):
    """Return the best temple action name."""
    if d <= 0 or gold <= 0:
        return 'none'
    best, act = camp(d - 1, max(0, gold - OVERHEAD), 0, 0, 0), 'end'
    for amt in (1, 5, 10, 20, 50):
        if amt > gold:
            continue
        ev = 0.0
        bonus = (1 if amt >= 10 else 0)
        for s, c in DIST2.items():
            t = s + bonus
            p = c / 36
            ng = max(0, gold - amt - OVERHEAD)
            if t >= 14:
                ev += p
            elif t == 7:
                ev += p * camp(d - 1, ng, 0, 0, 1)
            elif t in (12, 13):
                ev += p * max(camp(d - 1, ng, 0, 3, 0), camp(d - 1, ng, 0, 0, 0))
            else:
                ev += p * camp(d - 1, ng, 0, 0, 0)
        if ev > best:
            best, act = ev, amt
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
            ev += p * camp(d - 1, ng, 1 if t == 4 else 0, 0, 0)
        if ev > best:
            best, act = ev, 'news'
    return act


print('best temple action (perm=0), days left x gold:')
hdr = 'days\\gold ' + ''.join(f'{g:>6}' for g in range(10, CAP + 1, 20))
print(hdr)
for d in (5, 10, 15, 20, 25, 30, 40, 50, 60):
    print(f'{d:>9} ' + ''.join(f'{action(d, g):>6}' for g in range(10, CAP + 1, 20)))

travel = int(sys.argv[1]) if len(sys.argv) > 1 else 8
yield_ = float(sys.argv[2]) if len(sys.argv) > 2 else RUIN_YIELD
print(f'\nwin probability by ruin days (travel cost {travel} days, yield {yield_}):')
best = None
for ruin in range(0, TOTAL_DAYS - travel):
    temple = TOTAL_DAYS - ruin - travel
    gold = int(yield_ * ruin)
    w = camp(temple, gold, 0, 0, 0)
    if best is None or w > best[0]:
        best = (w, ruin, temple, gold)
    print(f'  ruin {ruin:>2}d -> temple {temple:>2}d, gold {gold:>4}, win {w:.3f}')
print(f'optimum: ruin {best[1]}d, temple {best[2]}d, gold {best[3]}, win {best[0]:.3f}')
