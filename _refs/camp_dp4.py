"""Definitive camp-phase DP with measured costs.

State: (days_left, gold, perm_omen, influence, temp_omen)
Daily overhead at a temple = food + lodging, measured at ~6 gold.

Actions:
  offer 1 / 5 / 10 / 20 / 50   (r212: 2d6 + 1 if >=10 + perm + omen + influence)
  seek news (r209)             (2d6 + 1, costs 5 gold; 4 -> permanent +1)
  do nothing

Prints the optimal policy so the bot's rules can be derived from it.
"""
from functools import lru_cache

DICE = {}
for a in range(1, 7):
    for b in range(1, 7):
        DICE[a + b] = DICE.get(a + b, 0) + 1
TOTAL = 36
OVERHEAD = 6
GOLD_CAP = 400
STEP = 5


def q(g):
    return min(GOLD_CAP, int(g // STEP) * STEP)


def news(f, d, gold, perm, infl, omen):
    if gold < 1:
        return f(d - 1, 0, perm, infl, omen)
    bonus = 1 if gold >= 5 else 0
    p = 0.0
    for dice, ways in DICE.items():
        total = min(12, dice + bonus)
        ng = q(max(0, gold - 5 - OVERHEAD))
        if total == 4:
            p += ways / TOTAL * f(d - 1, ng, 1, infl, omen)
        elif total == 3:
            p += ways / TOTAL * f(d - 1, q(ng + 50), perm, infl, omen)
        elif total == 8:
            p += ways / TOTAL * f(d - 1, q(ng // 2), perm, infl, omen)
        else:
            p += ways / TOTAL * f(d - 1, ng, perm, infl, omen)
    return p


def offer(f, d, gold, perm, infl, omen, amount):
    bonus = (1 if amount >= 10 else 0) + perm + omen + infl
    p = 0.0
    for dice, ways in DICE.items():
        total = dice + bonus
        ng = q(max(0, gold - amount - OVERHEAD))
        if total >= 14:
            p += ways / TOTAL
        elif total == 7:
            p += ways / TOTAL * f(d - 1, ng, perm, 0, 1)
        elif total in (12, 13):
            p += ways / TOTAL * f(d - 1, ng, perm, 3, 0)
        else:
            p += ways / TOTAL * f(d - 1, ng, perm, 0, 0)
    return p


@lru_cache(maxsize=None)
def best(d, gold, perm, infl, omen):
    if d == 0:
        return 0.0
    opts = [('nothing', f0(d - 1, q(max(0, gold - OVERHEAD)), perm, infl, omen))]
    opts.append(('news', news(best, d, gold, perm, infl, omen)))
    for a in (1, 5, 10, 20, 50):
        if a <= gold:
            opts.append((f'offer{a}', offer(best, d, gold, perm, infl, omen, a)))
    return max(v for _, v in opts)


def f0(d, gold, perm, infl, omen):
    return best(d, gold, perm, infl, omen)


def policy(d, gold, perm=0, infl=0, omen=0):
    opts = [('nothing', f0(d - 1, q(max(0, gold - OVERHEAD)), perm, infl, omen)),
            ('news', news(best, d, gold, perm, infl, omen))]
    for a in (1, 5, 10, 20, 50):
        if a <= gold:
            opts.append((f'offer{a}', offer(best, d, gold, perm, infl, omen, a)))
    opts.sort(key=lambda x: -x[1])
    return opts


print('=== camp value: days x gold (no omen) ===')
for d in (10, 15, 20, 25, 30, 40, 50):
    row = []
    for gold in (50, 100, 150, 200, 250, 300, 400):
        row.append(f'{best(d, q(gold), 0, 0, 0):.3f}')
    print(f'{d:>4} days: ' + '  '.join(row))
print()

print('=== optimal first move ===')
for d in (10, 15, 20, 30, 40, 50):
    for gold in (50, 100, 150, 200, 300, 400):
        top = policy(d, q(gold))
        print(f'{d:>4}d {gold:>4}g -> {top[0][0]} ({top[0][1]:.4f}) '
              f'| next: {top[1][0]} ({top[1][1]:.4f})')
print()

print('=== how long should we news-seek? (forced n news days, then optimal) ===')
for d in (20, 30, 40, 50):
    for gold in (100, 200, 300):
        best_n, best_p = 0, best(d, q(gold), 0, 0, 0)
        for n in range(1, d):
            g = max(0, gold - 11 * n)
            p = best(d - n, q(g), 1, 0, 0)
            if p > best_p:
                best_p, best_n = p, n
        print(f'{d:>4}d {gold:>4}g: best {best_n} news days -> {best_p:.4f}')
print()

print('=== full option ranking (days, gold) ===')
for d in (20, 30, 40):
    for gold in (100, 200, 300, 400):
        top = policy(d, q(gold))
        print(f'{d:>4}d {gold:>4}g: ' + ' | '.join(f'{k} {v:.4f}' for k, v in top))
print()

for d in (10, 20, 30, 40):
    for gold in (100, 200, 300):
        a = best(d, q(gold), 0, 0, 0)
        b = best(d, q(gold), 1, 0, 0)
        print(f'{d:>4}d {gold:>4}g: no omen {a:.4f}  omen {b:.4f}  x{b/a:.2f}')
