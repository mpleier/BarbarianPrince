import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import run

g = Game(seed=42)
run(g, 'aggressive', 6000)
for line in g.log:
    low = line.lower()
    if any(w in low for w in ('combat', 'fight', 'hire', 'hiring', 'loot',
                              'gold', 'staff', 'offering', 'dead', 'escape')):
        print(line)
