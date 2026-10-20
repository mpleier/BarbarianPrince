"""What is actually stopping the bot from winning?

For each seed it prints the day the party first reaches a temple, how many
offerings it makes, the distribution of offering totals, and the end state.
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
OFF = re.compile(r'Offering of (\d+) gold: dice (\d+) \+ (\d+) = (\d+)')

rows = []
totals = Counter()
for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    offs = [OFF.match(line) for line in g.log if OFF.search(line)]
    offs = [m for m in offs if m]
    for m in offs:
        totals[int(m.group(4))] += 1
    first_temple = next((i for i, line in enumerate(g.log)
                        if 'Offerings at' in line or 'temple' in line.lower()), None)
    rows.append((seed, g.day, g.gold, len(offs), g.won, g.reason, first_temple))

for r in rows:
    print(f'seed {r[0]:3} day {r[1]:3} gold {r[2]:4} offerings {r[3]:3} '
          f'won {r[4]}  {r[5]}')
print()
print('offering totals:', dict(sorted(totals.items())))
print('offerings per game: %.1f' % (sum(r[3] for r in rows) / N))
print('games that offered at all: %d' % sum(1 for r in rows if r[3]))
print('wins: %d' % sum(1 for r in rows if r[4]))
