"""Measure the ACTUAL gold yield of every action the engine performs.

Wraps Game.action() and records the gold delta attributable to each action,
plus the dice roll and the event code it resolved to.
"""
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

STATS = defaultdict(lambda: [0, 0, 0])   # action -> [count, gold, wins]
ROLLS = defaultdict(list)

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40

for s in range(1, N + 1):
    g = Game(seed=s)
    bot = Bot(g, 'balanced')
    orig_action = g.action

    def action(act, *a, **kw):
        before = g.gold
        res = orig_action(act, *a, **kw)
        STATS[act][0] += 1
        STATS[act][1] += g.gold - before
        return res
    g.action = action
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    STATS['WIN'][0] += 1 if g.won else 0

print(f'{len(STATS)} action types over {N} games')
for k, (c, gold, w) in sorted(STATS.items(), key=lambda x: -x[1][1]):
    print(f'{k:12} count {c:6}  gold {gold:8}  avg {gold / max(1, c):7.2f}')
print('wins:', STATS['WIN'][0])
