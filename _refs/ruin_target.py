"""Optimal ruin-phase gold target, using the exact camp DP as the fallback.

At a ruin with `d` days left and `g` gold the prince chooses between
  * camp now:  camp_value(d - travel, g)
  * mine one more day: E[ruin_value(d-1, g + delta)]
The gold threshold where mining stops is what the bot should aim for.
"""
import sys
sys.path.insert(0, 'src')
from functools import lru_cache
from camp_dp import camp_value

LOTTERY = [(0, 0.9733), (60, 0.0175), (500, 0.0097), (-10, 0.0005)]
TRAVEL = 12.2
WIT = True


@lru_cache(maxsize=None)
def ruin_value(days, gold):
    if days <= 0:
        return 0.0
    gold = min(gold, 400)
    camp = camp_value(max(0, int(days - TRAVEL)), gold, 0, 0, 0, WIT)
    if days <= 1:
        return camp
    mine = 0.0
    for delta, p in LOTTERY:
        mine += p * ruin_value(days - 1, gold + delta)
    return max(camp, mine)


def mining_target(days):
    """Highest gold at which one more ruin day is still worth it."""
    for g in range(400, -1, -1):
        camp = camp_value(max(0, int(days - TRAVEL)), g, 0, 0, 0, WIT)
        mine = sum(p * ruin_value(days - 1, g + delta) for delta, p in LOTTERY)
        if mine > camp:
            return g
    return 0


if __name__ == '__main__':
    print('days left at ruin | stop-mining gold target | P(win) from there')
    for d in range(10, 71, 5):
        print(f'  d={d:>2}  target={mining_target(d):>4}  P={ruin_value(d, 0):.3f}')

