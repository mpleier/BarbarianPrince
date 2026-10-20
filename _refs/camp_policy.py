"""Optimal r212 offering schedule from the exact camp DP.

OVERHEAD is the unavoidable food+lodging cost of a temple day, measured at
3 gold for a party of one (_refs/camp_cost.py).
"""
import sys, functools, collections
sys.stdout.reconfigure(encoding='utf-8')

DIST2 = collections.Counter(a + b for a in range(1, 7) for b in range(1, 7))
OVERHEAD = 3
CAP = 400

@functools.lru_cache(maxsize=None)
def camp(d, gold, perm, infl, omen):
    if d <= 0:
        return 0.0, None
    if gold <= 0:
        return 0.0, None
    best, act = 0.0, None
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
                ev += p * camp(d - 1, ng, perm, 0, 1)[0]
            elif t in (12, 13):
                ev += p * max(camp(d - 1, ng, perm, 3, 0)[0],
                              camp(d - 1, ng, perm, 0, 0)[0])
            else:
                ev += p * camp(d - 1, ng, perm, 0, 0)[0]
        if ev > best:
            best, act = ev, amt
    return best, act

def row(d, perm):
    out = []
    for g in range(10, CAP + 1, 10):
        out.append(camp(d, g, perm, 0, 0)[1])
    return out

print('optimal offering amount (perm=0)')
hdr = 'days\\gold ' + ''.join(f'{g:>5}' for g in range(10, CAP + 1, 10))
print(hdr)
for d in (5, 10, 15, 20, 25, 30, 40, 50, 60):
    print(f'{d:>8} ' + ''.join(f'{a:>5}' for a in row(d, 0)))
print()
print('win probability (perm=0)')
print(hdr)
for d in (5, 10, 15, 20, 25, 30, 40, 50, 60):
    print(f'{d:>8} ' + ''.join(f'{camp(d,g,0,0,0)[0]:>5.3f}' for g in range(10, CAP+1, 10)))
print()
print('win probability (perm=1)')
print(hdr)
for d in (5, 10, 15, 20, 25, 30, 40, 50, 60):
    print(f'{d:>8} ' + ''.join(f'{camp(d,g,1,0,0)[0]:>5.3f}' for g in range(10, CAP+1, 10)))
print()
print('gold needed before a 10-gold offering beats a 1-gold one:')
for d in range(2, 61):
    lo = next((g for g in range(1, CAP + 1)
               if (camp(d, g, 0, 0, 0)[1] or 0) >= 10), None)
    print(f'  days={d:>2}: gold >= {lo}')


