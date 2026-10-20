"""Measure the true per-search gold distribution of r208 from the engine.

Runs thousands of isolated ruin searches in a temple/ruins hex and records the
gold delta, so the bot's weights use measured numbers rather than guesses.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game

TRIALS = 4000
dist = Counter()
total = 0
for s in range(TRIALS):
    g = Game(seed=s)
    # force the party into a ruins hex with the starting prince only
    g.hex = '0307'
    g.visited.add('0307')
    before = g.gold
    g._ruins_retry = 0
    g.search_ruins()
    d = g.gold - before
    dist[d] += 1
    total += d

print(f'{TRIALS} ruin searches, mean {total / TRIALS:.2f} gold/search')
for d, c in sorted(dist.items()):
    print(f'  {d:6} gold  {c:5}  {c / TRIALS:.4f}')
