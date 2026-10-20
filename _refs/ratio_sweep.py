"""Sweep RUIN_RATIO (and MIN_CAMP_DAYS) against the real engine.

The macro DP (_refs/macro_dp5.py) says the ruin phase should be bounded by the
gold target, not by a fixed share of the campaign: mining is free and camping
with no gold is worthless, so the party should keep digging until the target is
reached or the camp would be too short.  This measures what that actually buys.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import autoplay
from engine import Game
from autoplay import Bot


def batch(n, ratio, min_camp):
    autoplay.RUIN_RATIO = ratio
    autoplay.MIN_CAMP_DAYS = min_camp
    wins = ruin = camp = gold = 0
    broke = 0
    for seed in range(1, n + 1):
        g = Game(seed=seed)
        b = Bot(g, 'balanced')
        g.run_until_idle(max_steps=6000, chooser=b.choose)
        wins += g.staff
        ruin += b.ruin_days
        camp += sum(1 for l in g.log if 'Offering of' in l)
        gold += g.gold
        if g.gold < 10:
            broke += 1
    return wins / n, ruin / n, camp / n, gold / n, broke / n


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    ratios = [float(x) for x in sys.argv[2:]] or [0.56, 0.7, 0.85, 1.0]
    print(f'{"ratio":>6} {"min_camp":>9} {"win":>7} {"ruin":>6} {"offer":>6} '
          f'{"gold":>6} {"broke":>6}')
    for ratio in ratios:
        for mc in (5, 10):
            w, r, c, g, b = batch(n, ratio, mc)
            print(f'{ratio:>6} {mc:>9} {w:>7.3f} {r:>6.1f} {c:>6.1f} '
                  f'{g:>6.1f} {b:>6.3f}')
