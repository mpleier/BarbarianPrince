"""The exact macro decision at the ruin: mine one more day, or walk to camp.

The camp DP (_refs/camp_dp_exact.py) gives P(win) for any (camp days, gold).
Ruins are the only source of gold in the campaign (_refs/gold_flow.py), and a
search is a lottery: 97.3% nothing, 1.7% 60 gold, 1.1% 500 gold
(_refs/ruin_cost.py).  So the ruin phase is a stopping problem - at every day
the party either takes another ticket or walks to the temple and starts
spending.  This solves it exactly and prints the resulting policy as a table of
"keep mining while gold <= X" thresholds, plus the win probability the policy
achieves against the real lottery.
"""
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '_refs')
sys.stdout.reconfigure(encoding='utf-8')

from functools import lru_cache

TOTAL_DAYS = 70
START_TO_RUIN = float(sys.argv[1]) if len(sys.argv) > 1 else 12.2
RUIN_TO_TEMPLE = float(sys.argv[2]) if len(sys.argv) > 2 else 10.8
GOLD_CAP = 400

# measured in _refs/ruin_cost.py over 3000 engine searches
LOTTERY = [(0, 0.9727), (60, 0.0167), (500, 0.0107)]

from camp_dp_exact import value as camp


@lru_cache(maxsize=None)
def ruin_value(d, g):
    """P(win) with d days left, g gold, standing on the ruin."""
    if d <= 0:
        return 0.0
    camp_option = camp(max(0, d - RUIN_TO_TEMPLE), min(g, GOLD_CAP), 0, 0, 0)
    if d <= RUIN_TO_TEMPLE:
        return camp_option
    mine = 0.0
    for amount, p in LOTTERY:
        mine += p * ruin_value(d - 1, min(GOLD_CAP, g + amount))
    return max(camp_option, mine)


@lru_cache(maxsize=None)
def mine_days_left(d, g):
    """How many more days of mining the optimal policy takes from (d, g)."""
    if d <= RUIN_TO_TEMPLE:
        return 0
    if ruin_value(d, g) <= camp(d - RUIN_TO_TEMPLE, min(g, GOLD_CAP), 0, 0, 0) + 1e-12:
        return 0
    best = max((p * ruin_value(d - 1, min(GOLD_CAP, g + a))
                for a, p in LOTTERY))
    return 1 + mine_days_left(d - 1, g) if best > camp_option_of(d, g) else 1


def camp_option_of(d, g):
    return camp(max(0, d - RUIN_TO_TEMPLE), min(g, GOLD_CAP), 0, 0, 0)


def expected_win(d, g):
    """Simulate the optimal policy forward against the lottery."""
    if d <= RUIN_TO_TEMPLE:
        return camp(max(0, d - RUIN_TO_TEMPLE), min(g, GOLD_CAP), 0, 0, 0)
    if ruin_value(d, g) == camp_option_of(d, g):
        return camp_option_of(d, g)
    return sum(p * expected_win(d - 1, min(GOLD_CAP, g + a))
               for a, p in LOTTERY)


pool = TOTAL_DAYS - START_TO_RUIN
print(f'travel: start->ruin {START_TO_RUIN}, ruin->temple {RUIN_TO_TEMPLE}, '
      f'mining+camping pool {pool:.1f} days')
print(f'optimal P(win) from the start: {expected_win(pool, 0):.4f}\n')

print('days left at ruin | keep mining while gold <=  | P(win) if we go now')
for d in range(int(pool), int(RUIN_TO_TEMPLE), -1):
    thresh = 0
    for g in range(0, GOLD_CAP + 1, 5):
        if ruin_value(d, g) > camp_option_of(d, g) + 1e-12:
            thresh = g
    print(f'  {d:>3}            gold <= {thresh:>4}              '
          f'{camp_option_of(d, 0):.3f}')

print('\nexpected mining days under the optimal policy from (pool, 0):',
      mine_days_left(pool, 0))
print('distribution of gold when the policy walks to camp:')
seen = {}
def dist(d, g, p):
    if d <= RUIN_TO_TEMPLE or ruin_value(d, g) == camp_option_of(d, g):
        seen[g] = seen.get(g, 0) + p
        return
    for a, q in LOTTERY:
        dist(d - 1, min(GOLD_CAP, g + a), p * q)
dist(pool, 0, 1.0)
for g, p in sorted(seen.items()):
    print(f'  {g:>4} gold  {p:.4f}')
print(f'expected gold at camp {sum(g * p for g, p in seen.items()):.1f}')
print(f'P(arrive with < 10 gold) {sum(p for g, p in seen.items() if g < 10):.3f}')
