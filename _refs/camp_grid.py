"""Camp win-rate grid: P(win) as a function of camp days and gold.

Measured with the real engine, so it includes food, lodging, desertion, the
High Priest, exile on a 10, and death on a 2.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot
from camp_policy_test import temple_of, policy_choice


def win(seed, gold, day):
    g = Game(seed=seed)
    g.gold = gold
    g.day = day
    g.hex = temple_of(g)
    if g.hex is None:
        return False
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    return g.staff


N = int(sys.argv[1]) if len(sys.argv) > 1 else 150
GOLDS = [0, 20, 40, 60, 80, 100, 150, 200, 300, 400]
print('camp_days  ' + '  '.join(f'{g:>4}' for g in GOLDS))
grid = {}
for days_left in (5, 10, 15, 20, 25, 30, 35, 40, 45, 50):
    day = 70 - days_left + 1
    row = []
    for gold in GOLDS:
        w = sum(1 for s in range(1, N + 1) if win(s, gold, day))
        row.append(w / N)
    grid[days_left] = row
    print(f'{days_left:>9}  ' + '  '.join(f'{x:.3f}' for x in row))

import json
json.dump(grid, open('_refs/camp_grid.json', 'w'))
print('\nsaved to _refs/camp_grid.json')
