"""Exact DP for the optimal temple-camp policy.

At a temple each day you may either:
  - seek news (r209, 2d6 + gold/wit bonus): 4 -> permanent +1 to offerings,
    3 -> +50 gold, 8 -> lose half your wealth
  - make an offering (r212, 2d6 + 1 if 10+ gold + omen + influence)

We compute the exact win probability for a given number of remaining days and
gold, so the bot's weights can be set from the real optimum.
"""
from functools import lru_cache

DICE = {}
for a in range(1, 7):
    for b in range(1, 7):
        DICE[a + b] = DICE.get(a + b, 0) + 1
TOTAL = 36

NEWS = {2: 'nothing', 3: 'gold50', 4: 'omen', 5: 'local', 6: 'caravan',
        7: 'cheap', 8: 'lose_half', 9: 'constabulary', 10: 'magician',
        11: 'thieves', 12: 'informant'}


def camp(days, gold, news_bonus, news_spend=True):
    """news_bonus: +1 to the news roll (gold>=5 and/or wit>=5)."""
    nb = news_bonus

    @lru_cache(maxsize=None)
    def f(d, gold, perm, infl, omen):
        if d == 0:
            return 0.0
        best = 0.0
        # --- offering ---
        for amount in (1, 5, 10, 20, 50):
            if amount > gold:
                continue
            bonus = (1 if amount >= 10 else 0) + perm + omen + infl
            p = 0.0
            for dice, ways in DICE.items():
                total = dice + bonus
                if total >= 14:
                    p += ways / TOTAL
                elif total == 7:
                    p += ways / TOTAL * f(d - 1, gold - amount, perm, 0, 1)
                elif total in (12, 13):
                    p += ways / TOTAL * f(d - 1, gold - amount, perm, 3, 0)
                else:
                    p += ways / TOTAL * f(d - 1, gold - amount, perm, 0, 0)
            best = max(best, p)
        # --- news ---
        p = 0.0
        for dice, ways in DICE.items():
            total = min(12, max(2, dice + nb))
            r = NEWS[total]
            if r == 'omen':
                p += ways / TOTAL * f(d - 1, gold, 1, infl, omen)
            elif r == 'gold50':
                p += ways / TOTAL * f(d - 1, gold + 50, perm, infl, omen)
            elif r == 'lose_half':
                p += ways / TOTAL * f(d - 1, gold // 2, perm, infl, omen)
            else:
                p += ways / TOTAL * f(d - 1, gold, perm, infl, omen)
        best = max(best, p)
        return best
    return f(days, gold, 0, 0, 0)


print('Optimal camp policy: P(win) vs days and starting gold')
print(f'{"days":>5} {"gold":>6} {"news+0":>8} {"news+1":>8} {"offer-only":>10}')
for days in (10, 20, 30, 40, 50, 60):
    for gold in (0, 50, 100, 200):
        a = camp(days, gold, 0)
        b = camp(days, gold, 1)
        print(f'{days:>5} {gold:>6} {a:>8.4f} {b:>8.4f}')
    print()
