"""Exact ruin-stopping DP vs the one-step greedy rule used by camp_dp.

Both are evaluated on the same measured ruins lottery, so the difference is
purely the lookahead: `ruin_should_mine` compares today's camp value with the
camp value after one more dig, while the exact DP compares it with the optimal
value of every future dig.
"""
import sys
sys.path.insert(0, 'src')

from functools import lru_cache

from camp_dp import camp_value, ruin_should_mine

# Measured over 20,000 searches in _refs/ruin_dist.py.
LOTTERY = [(0, 0.9733), (60, 0.0175), (500, 0.0097), (1000, 0.0005)]
LOTTERY = [(g, p / sum(p for _, p in LOTTERY)) for g, p in LOTTERY]

CAP = 400


def camp(days, gold):
    return camp_value(max(0, days), min(gold, CAP), 0, 0, 0, False)


@lru_cache(maxsize=None)
def exact(days, gold, travel):
    """Optimal P(win) standing at a ruin."""
    stay = camp(days - travel, gold)
    if days <= travel:
        return stay
    dig = 0.0
    for gain, prob in LOTTERY:
        if prob > 0:
            dig += prob * exact(days - 1, min(gold + gain, CAP), travel)
    return max(stay, dig)


def greedy_value(days, gold, travel):
    """P(win) of the one-step-lookahead policy actually used by the bot."""
    if days <= travel or not ruin_should_mine(days, gold, travel):
        return camp(days - travel, gold)
    ev = 0.0
    for gain, prob in LOTTERY:
        if prob > 0:
            ev += prob * greedy_value(days - 1, min(gold + gain, CAP), travel)
    return ev


def exact_days(days, gold, travel):
    """Mining days the exact DP takes along the 'nothing found' path."""
    if days <= travel:
        return 0
    dig = sum(p * exact(days - 1, min(gold + g, CAP), travel)
              for g, p in LOTTERY if p > 0)
    if dig > camp(days - travel, gold):
        return 1 + exact_days(days - 1, gold, travel)
    return 0


def greedy_days(days, gold, travel):
    if days <= travel or not ruin_should_mine(days, gold, travel):
        return 0
    return 1 + greedy_days(days - 1, gold, travel)


if __name__ == '__main__':
    for travel in (6, 8, 10, 12):
        days = 70 - 13 + 1
        print(f'travel {travel:2}: exact {exact(days, 0, travel):.4f}  '
              f'greedy {greedy_value(days, 0, travel):.4f}  '
              f'exact mine-days {exact_days(days, 0, travel):3}  '
              f'greedy mine-days {greedy_days(days, 0, travel):3}')
    print()
    for days in (30, 40, 50, 58):
        for travel in (8, 10):
            lo, hi = 0, 400
            while lo < hi:
                mid = (lo + hi) // 2
                if exact_days(days, mid, travel) > 0:
                    lo = mid + 1
                else:
                    hi = mid
            g = 0
            while ruin_should_mine(days, g, travel) and g < 400:
                g += 1
            print(f'days {days:2} travel {travel:2}: exact stop at gold {lo:4}, '
                  f'greedy stop at gold {g:4}')
