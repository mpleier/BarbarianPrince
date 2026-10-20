"""Macro plan DP: mining days vs camping days with the real ruins lottery.

``_refs/ruin_dist.py`` measures the actual yield of a ruins search in the
engine: 97.3% of days give nothing, 1.75% give 60, 0.97% give 500.  A mean of
5.9 gold/day hides that variance, and variance matters because the camp value
function is concave in gold - a 500 gold windfall is worth far less than five
100-gold days would suggest.

``_refs/camp_dp_exact.py`` gives the exact P(win) of a camp of ``c`` days
starting with ``g`` gold.  This script maximises

    E[ camp(c, g + yield_of_mining_days) ]

over the number of mining days, and then extracts the gold threshold at which
the bot should stop mining for each amount of time left.
"""
import sys
from functools import lru_cache

sys.path.insert(0, 'src')
sys.path.insert(0, '_refs')

from camp_dp_exact import value as camp

YIELDS = [(0.9728, 0), (0.0175, 60), (0.0097, 500)]
GOLD_MAX = 420
# _refs/map_probe.py: the ruin chosen by plan() is ~4 expected days away and
# the temple paired with it ~6 days further, so walking costs about 10 days of
# the 70-day campaign.  Both numbers are command-line overridable.
TRAVEL_TO_TEMPLE = float(sys.argv[1]) if len(sys.argv) > 1 else 10.8
TRAVEL_TO_RUIN = float(sys.argv[2]) if len(sys.argv) > 2 else 12.2
TOTAL = 70


def camp_capped(c, g):
    return camp(c, min(g, GOLD_MAX), 0, 0, 0)


@lru_cache(maxsize=None)
def value(days, gold, at_ruin):
    """Best win probability with `days` left and `gold` in hand.

    at_ruin=True  -> the party is standing on the ruins hex.
    at_ruin=False -> the party still has to walk TRAVEL_TO_RUIN days to reach it.
    """
    if days <= 0:
        return 0.0
    if not at_ruin:
        return value(days - 1, gold, True)

    # Option 1: walk to the temple and camp out the rest of the campaign.
    camp_days = max(0, days - TRAVEL_TO_TEMPLE)
    best = camp_capped(camp_days, gold)

    # Option 2: spend one more day mining, then decide again.
    if days > TRAVEL_TO_TEMPLE + 1:
        ev = 0.0
        for p, y in YIELDS:
            ev += p * value(days - 1, gold + y, True)
        best = max(best, ev)
    return best


pool = TOTAL - TRAVEL_TO_RUIN

print('Lottery model: expected P(win) by number of mining days')
for r in range(0, 46, 3):
    dist = {0: 1.0}
    for _ in range(r):
        nxt = {}
        for g, p in dist.items():
            for q, y in YIELDS:
                nxt[g + y] = nxt.get(g + y, 0) + p * q
        dist = nxt
    camp_days = pool - TRAVEL_TO_TEMPLE - r
    ev = sum(p * camp_capped(camp_days, g) for g, p in dist.items())
    print(f'  mine {r:2d} days -> P(win) {ev:.3f}')

print('\nStop-mining gold threshold (mining one more day vs going straight to camp):')
for days in range(12, 62, 4):
    thresholds = []
    for gold in range(0, GOLD_MAX + 1, 5):
        mine = 0.0
        for p, y in YIELDS:
            mine += p * value(days - 1, gold + y, True)
        camp_now = camp_capped(max(0, days - TRAVEL_TO_TEMPLE), gold)
        if mine > camp_now:
            thresholds.append(gold)
    hi = max(thresholds) if thresholds else 0
    print(f'  days left {days:2d}: keep mining while gold <= {hi}')
