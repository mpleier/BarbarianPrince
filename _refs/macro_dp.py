"""Macro plan DP: how many days to farm ruins before committing to a temple.

Measured economics (from gold_days.py over 150 campaigns):
  ruin day   : +5.5 gold net
  temple day : -5.5 gold net (offering + food + lodging)
  travel day : ~1 day, small gold cost

For every (days_left, gold, travel_days_to_nearest_temple) we compute the
optimal number of ruin days R, then evaluate best(C, gold + 5.5R) with
C = days_left - R - travel, using the exact camp DP from camp_dp4.
"""
import sys
sys.path.insert(0, '.')
from camp_dp4 import best, q

RUIN_YIELD = 5.5
TEMPPLE_COST = 5.5
DAYS = 70


def plan(days_left, gold, travel):
    """Return (win_prob, R) for the best ruin-farming duration."""
    best_p, best_r = -1, 0
    for R in range(0, max(0, days_left - travel) + 1):
        C = days_left - R - travel
        if C < 0:
            continue
        g = gold + RUIN_YIELD * R
        # the camp DP already models gold depletion, so just feed it the bank
        p = best(C, q(g), 0, 0, 0)
        if p > best_p:
            best_p, best_r = p, R
    return best_p, best_r


print('Optimal ruin days R (and win prob) for a party at a ruin:')
print(f'{"days_left":>10} {"gold":>6} {"travel":>7} -> {"R":>4} {"C":>4} {"win":>7}')
for days_left in (70, 60, 50, 40, 30, 20):
    for gold in (0, 50, 100, 150, 200, 300):
        for travel in (4, 6, 8):
            p, R = plan(days_left, gold, travel)
            print(f'{days_left:>10} {gold:>6} {travel:>7} -> {R:>4} '
                  f'{days_left-R-travel:>4} {p:>7.4f}')
    print()
