"""What the camp DP actually decides at the ruin.

For a party standing at a ruin with `days` campaign days left and `travel`
expected days of walking to the nearest temple, report the DP-optimal number of
mining days and the resulting win probability, so the live bot's 31-day average
can be compared with the theoretical optimum.
"""
import sys
sys.path.insert(0, 'src')

from functools import lru_cache

from camp_dp import camp_value, LOTTERY


def camp(days, gold):
    """Win probability of camping `days` days with `gold` and no modifiers."""
    return camp_value(max(0, days), min(gold, 400), 0, 0, 0, False)


@lru_cache(maxsize=None)
def ruin_value(days, gold, travel):
    """Exact optimal value at a ruin (one-day-per-step stopping problem)."""
    value = camp(days - travel, gold)
    if days <= travel:
        return value
    ev = 0.0
    for gain, prob in LOTTERY:
        if prob > 0:
            ev += prob * ruin_value(days - 1, min(gold + gain, 400), travel)
    return max(value, ev)


def policy_days(days, gold, travel):
    """Mining days the DP takes along the "nothing found" path."""
    if days <= travel:
        return 0
    value = camp(days - travel, gold)
    ev = sum(p * ruin_value(days - 1, min(gold + g, 400), travel)
             for g, p in LOTTERY if p > 0)
    if ev > value:
        return 1 + policy_days(days - 1, gold, travel)
    return 0


def main():
    for travel in (6, 8, 10, 12, 14):
        for start_day in (12, 16, 20):
            days = 70 - start_day + 1
            print(f'travel {travel:2}  arrive ruin day {start_day:2}  '
                  f'days left {days:2}  DP value {ruin_value(days, 0, travel):.4f}  '
                  f'mine days (no-hit path) {policy_days(days, 0, travel):3}  '
                  f'camp-only {camp(days - travel, 0):.4f}')


if __name__ == '__main__':
    main()
