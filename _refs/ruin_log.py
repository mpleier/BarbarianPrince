"""Dump the raw engine log for one seed, filtered to ruins searches."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
g = Game(seed=seed)
bot = Bot(g, 'balanced')
g.run_until_idle(max_steps=6000, chooser=bot.choose)
for line in g.log:
    low = line.lower()
    if 'ruin' in low or 'treasure' in low or 'gold' in low:
        print(line)
print('final gold', g.gold)
