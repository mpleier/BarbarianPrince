"""Monte-Carlo the r212 offering chain at a temple.

The engine rolls 2d6 for offerings (r212), so a 14+ needs modifiers:
  +1  for offering 10+ gold
  +1  permanent, from the news omen (r209 result 4)
  +1  temporary, from a previous offering that rolled exactly 7
  +3  temporary, from the High Priest's influence (offering rolled 12 or 13)

This simulates "camp at a temple and offer every day" and measures the
probability of winning as a function of days spent and gold available.
"""
import random
from collections import Counter

TRIALS = 20000
rng = random.Random(7)


def offer_chain(days, gold, perm_omen, policy='always10'):
    """Return True if the staff is won within `days` at one temple."""
    influence = 0
    omen = 0
    for _ in range(days):
        if policy == 'always10':
            amount = 10 if gold >= 10 else 0
        else:
            amount = 10 if gold >= 10 else 1
        if amount == 0:
            return False
        gold -= amount
        bonus = (1 if amount >= 10 else 0) + perm_omen + omen + influence
        total = rng.randint(1, 6) + rng.randint(1, 6) + bonus
        omen = 0
        influence = 0
        if total >= 14:
            return True
        if total == 7:
            omen = 1
        elif total in (12, 13):
            influence = 3
    return False


for perm in (0, 1):
    for days in (10, 20, 30, 40, 50, 60):
        gold = 10 * days
        wins = sum(1 for _ in range(TRIALS) if offer_chain(days, gold, perm))
        print(f'perm_omen={perm} days={days:3} gold={gold:4}  win {wins / TRIALS:.3f}')
    print()

# How often does a 10-gold offering chain actually reach 14+?
totals = Counter()
for _ in range(TRIALS * 30):
    totals[rng.randint(1, 6) + rng.randint(1, 6) + 2] += 1
print('2d6+2 distribution:', dict(sorted(totals.items())))
