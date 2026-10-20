"""Exact DP for the r212 offering chain.

State: (gold, influence, omen) with the permanent news omen as a parameter.
Each day at the temple we choose an offering amount; the roll is 2d6 + bonus.
We compute the exact probability of winning within D days.
"""
from functools import lru_cache

DICE = {}
for a in range(1, 7):
    for b in range(1, 7):
        DICE[a + b] = DICE.get(a + b, 0) + 1
TOTAL = 36


def win_prob(days, gold, perm_omen, amount_choice='best'):
    @lru_cache(maxsize=None)
    def f(d, gold, infl, omen):
        if d == 0:
            return 0.0
        best = 0.0
        for amount in (1, 5, 10, 20, 50):
            if amount > gold:
                continue
            bonus = (1 if amount >= 10 else 0) + perm_omen + omen + infl
            p = 0.0
            for dice, ways in DICE.items():
                total = dice + bonus
                if total >= 14:
                    p += ways / TOTAL
                elif total == 7:
                    p += ways / TOTAL * f(d - 1, gold - amount, 0, 1)
                elif total in (12, 13):
                    p += ways / TOTAL * f(d - 1, gold - amount, 3, 0)
                else:
                    p += ways / TOTAL * f(d - 1, gold - amount, 0, 0)
            best = max(best, p)
        return best
    return f(days, gold, 0, 0)


print('Exact P(win) by days-at-temple and gold banked')
print(f'{"days":>5} {"gold":>6} {"no omen":>9} {"news omen":>10}')
for days in (10, 20, 30, 40, 50, 60):
    for gold in (10 * days, 200, 100, 50):
        if gold > 10 * days:
            continue
        a = win_prob(days, gold, 0)
        b = win_prob(days, gold, 1)
        print(f'{days:>5} {gold:>6} {a:>9.4f} {b:>10.4f}')
    print()
