"""Does the bot pick the ruin the DP would pick?

`Bot.plan()` maximises the number of camp days, but the real objective is
`ruin_value(days_left_at_ruin, 0, ruin_to_temple)` - the win probability of the
optimal mine-then-camp policy.  A ruin that is a day further from the start but
three days closer to a temple can be worth more even though it leaves fewer
camp days, because the mining lottery is played with the travel already paid
for.

This compares the two choices over many campaigns and reports the win
probability each would have achieved.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot, TOTAL_DAYS
from camp_dp import ruin_value


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    plan = b.plan()
    if not plan:
        return None
    best = None
    for r, p in g.features['places'].items():
        if p['kind'] != 'ruins':
            continue
        t, td = b.nearest('temple', r)
        days = (TOTAL_DAYS - g.day + 1) - b.travel_days(r).get(g.hex, 999.0)
        v = ruin_value(int(max(0, days)), 0, td)
        if best is None or v > best[1]:
            best = (r, v, td)
    _, bot_ruin, bot_temple = plan
    bot_td = b.travel_days(bot_temple).get(bot_ruin, 999.0)
    bot_days = (TOTAL_DAYS - g.day + 1) - b.travel_days(bot_ruin).get(g.hex, 999.0)
    bot_v = ruin_value(int(max(0, bot_days)), 0, bot_td)
    return bot_v, best[1] if best else 0.0, plan[0]


def main(n):
    bot_sum = dp_sum = 0.0
    better = 0
    for s in range(1, n + 1):
        r = run(s)
        if not r:
            continue
        bot_v, dp_v, camp_days = r
        bot_sum += bot_v
        dp_sum += dp_v
        if dp_v > bot_v + 1e-9:
            better += 1
    print(f'{n} campaigns')
    print(f'  bot ruin choice  : mean P(win) {bot_sum/n:.4f}')
    print(f'  DP ruin choice   : mean P(win) {dp_sum/n:.4f}')
    print(f'  campaigns where the DP prefers a different ruin: {better}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
