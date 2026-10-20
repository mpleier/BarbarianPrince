"""Monte-Carlo check of the camp DP, so the DP's numbers can be trusted."""
import random
from functools import lru_cache

DICE = {}
for a in range(1, 7):
    for b in range(1, 7):
        DICE[a + b] = DICE.get(a + b, 0) + 1
TOTAL = 36
LODGING = 2


def simulate(days, gold, amount, perm=False, trials=200000, rng=None):
    rng = rng or random.Random(7)
    wins = 0
    for _ in range(trials):
        g, p, i, o = gold, perm, 0, 0
        for _ in range(days):
            if g < amount:
                break
            g -= amount
            bonus = (1 if amount >= 10 else 0) + p + o + i
            total = rng.randint(1, 6) + rng.randint(1, 6) + bonus
            o = i = 0
            if total >= 14:
                wins += 1
                break
            if total == 7:
                o = 1
            elif total in (12, 13):
                i = 3
            g -= LODGING
            if g < 0:
                break
    return wins / trials


@lru_cache(maxsize=None)
def dp(d, gold, perm, infl, omen, amount):
    if d == 0 or gold < amount:
        return 0.0
    bonus = (1 if amount >= 10 else 0) + perm + omen + infl
    p = 0.0
    for dice, ways in DICE.items():
        total = dice + bonus
        ng = gold - amount - LODGING
        if total >= 14:
            p += ways / TOTAL
        elif total == 7:
            p += ways / TOTAL * dp(d - 1, ng, perm, 0, 1, amount)
        elif total in (12, 13):
            p += ways / TOTAL * dp(d - 1, ng, perm, 3, 0, amount)
        else:
            p += ways / TOTAL * dp(d - 1, ng, perm, 0, 0, amount)
    return p


for days, gold, amount, perm in ((30, 300, 1, False), (30, 300, 10, False),
                                 (30, 300, 10, True), (20, 200, 10, False)):
    print(f'{days}d {gold}g amount={amount} perm={perm}: '
          f'dp {dp(days, gold, int(perm), 0, 0, amount):.4f}  '
          f'mc {simulate(days, gold, amount, perm):.4f}')
