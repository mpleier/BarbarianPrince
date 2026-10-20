"""Sweep the macro knobs of the bot and measure the win rate.

RUIN_RATIO decides how much of the non-travel pool is spent mining; MIN_CAMP_DAYS
decides when the party stops mining and walks to a temple.  Both are constants in
src/autoplay.py, so the sweep patches them before each batch of campaigns.
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
    wins = 0
    ruin_days = 0
    camp_days = 0
    gold = 0
    for seed in range(1, n + 1):
        g = Game(seed=seed)
        b = Bot(g, 'balanced')
        g.run_until_idle(max_steps=6000, chooser=b.choose)
        wins += g.staff
        ruin_days += b.ruin_days
        camp_days += sum(1 for l in g.log if 'Offering' in l)
        gold += g.gold
    return wins / n, ruin_days / n, camp_days / n, gold / n


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    print(f'{"ratio":>6} {"min_camp":>9} {"win":>7} {"ruin":>6} {"offer":>6} {"gold":>6}')
    for ratio in (0.35, 0.45, 0.56, 0.65, 0.75, 0.85):
        for mc in (5, 10, 15):
            w, r, c, g = batch(n, ratio, mc)
            print(f'{ratio:>6} {mc:>9} {w:>7.3f} {r:>6.1f} {c:>6.1f} {g:>6.1f}')
