"""Should a temple day be spent offering (r212) or seeking news (r209)?

r209 with 5+ gold spent: 2d6+1.  3 -> +50 gold, 4 -> permanent +1 to every
future offering, 8 -> lose half your wealth.  The permanent +1 is the single
biggest lever in the game, so this DP compares it against burning a day on an
offering.
"""
import sys, functools, collections
sys.stdout.reconfigure(encoding='utf-8')

DIST2 = collections.Counter(a + b for a in range(1, 7) for b in range(1, 7))
OVERHEAD = 3
CAP = 400


@functools.lru_cache(maxsize=None)
def best(d, gold, perm, infl, omen):
    if d <= 0:
        return 0.0, None
    if gold <= 0:
        return 0.0, None
    out, act = 0.0, None
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
                ev += p * best(d - 1, ng, perm, 0, 1)[0]
            elif t in (12, 13):
                ev += p * max(best(d - 1, ng, perm, 3, 0)[0],
                             best(d - 1, ng, perm, 0, 0)[0])
            else:
                ev += p * best(d - 1, ng, perm, 0, 0)[0]
        if ev > out:
            out, act = ev, ('offer', amt)
    # news: spend 5 gold, roll 2d6+1
    if gold >= 5:
        ng0 = max(0, gold - 5 - OVERHEAD)
        ev = 0.0
        for s, c in DIST2.items():
            t = s + 1
            p = c / 36
            if t == 3:
                ev += p * best(d - 1, min(CAP, ng0 + 50), perm, 0, 0)[0]
            elif t == 4:
                ev += p * best(d - 1, ng0, 1, 0, 0)[0]
            elif t == 8:
                ev += p * best(d - 1, ng0 // 2, perm, 0, 0)[0]
            else:
                ev += p * best(d - 1, ng0, perm, 0, 0)[0]
        if ev > out:
            out, act = ev, 'news'
    return out, act


print('days  gold   100  150  200  250  300  350  400   (optimal action, win prob)')
for d in (10, 15, 20, 25, 30, 35, 40, 45, 50):
    row = f'{d:>4}      '
    for g in (100, 150, 200, 250, 300, 350, 400):
        v, a = best(d, g, 0, 0, 0)
        row += f'{a[1] if a and a[0] == "offer" else "N":>4}'
    print(row)

print()
print('news (N) vs offering (1/10) - rows are camp days, columns starting gold:')
hdr = 'days\\gold ' + ''.join(f'{g:>5}' for g in (20, 40, 60, 80, 100, 150, 200, 250, 300, 400))
print(hdr)
for d in (5, 10, 15, 20, 25, 30, 40, 50, 60):
    row = f'{d:>8} '
    for g in (20, 40, 60, 80, 100, 150, 200, 250, 300, 400):
        v, a = best(d, g, 0, 0, 0)
        row += f'{(a[1] if a and a[0] == "offer" else "N"):>5}'
    print(row)

print()
print('value of the permanent omen (perm=1 vs perm=0):')
for d in (10, 20, 30, 40):
    for g in (100, 200, 300):
        print(f'  days={d:>2} gold={g:>3}: {best(d,g,0,0,0)[0]:.3f} -> {best(d,g,1,0,0)[0]:.3f}')
