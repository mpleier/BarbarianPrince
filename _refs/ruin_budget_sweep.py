"""Sweep a fixed ruin-mining budget against the live engine.

Replaces the bot's DP-driven `mining()` with "dig until B ruin days are spent",
so the optimal number of mining days can be measured empirically instead of
assumed.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot


def win_rate(budget, n=200, strategy='balanced'):
    wins = 0
    days = []
    gold = []
    temple = 0
    for seed in range(1, n + 1):
        g = Game(seed=seed)
        b = Bot(g, strategy)
        b.mining = lambda: b.ruin_days < budget
        try:
            g.run_until_idle(max_steps=6000, chooser=b.choose)
        except Exception:
            continue
        if g.staff:
            wins += 1
        days.append(g.day)
        gold.append(g.gold)
        temple += sum(1 for h in b.path if g.place_kind(h) == 'temple')
    return wins / n, sum(days) / len(days), sum(gold) / len(gold)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    budgets = [int(x) for x in sys.argv[2:]] or list(range(10, 46, 5))
    for b in budgets:
        r, d, g = win_rate(b, n)
        print(f'budget {b:3}  win {r:.3f}  avg end day {d:5.1f}  avg gold {g:6.1f}')
