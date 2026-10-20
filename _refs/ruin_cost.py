"""What a ruins search really costs and pays.

`ruin_dist.py` measured the raw treasure table (97.3% nothing, 1.75% 60 gold,
0.97% 500 gold), but a search also rolls encounters (r208 result 12/13 sends
the party into e035 "unclean ruins"), and those encounters can cost gold.  This
script histograms the *net* gold of one search and prints the log of the
searches that lost money.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')

import random
from collections import Counter
from engine import Game
from autoplay import Bot

TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
g = Game(seed=11)
g.gold = 100000
g.hex = '0307'
b = Bot(g, 'balanced')
g.party = [c for c in g.party if c.prince]

hist = Counter()
worst = []
for _ in range(TRIALS):
    before = g.gold
    g.search_ruins()
    while g.prompts:
        p = g.prompts[-1]
        g.prompts.pop()
        handler = p.get('handler')
        if handler:
            handler(b.choose(p, record=False))
    delta = g.gold - before
    hist[delta] += 1
    if delta < 0 and len(worst) < 6:
        worst.append(g.log[-14:])

print('net gold per ruins search:')
for d, c in sorted(hist.items()):
    print(f'  {d:>6} gold  {c / TRIALS:.4f}')
print(f'mean {sum(d * c for d, c in hist.items()) / TRIALS:.3f}')
print()
for w in worst:
    print('--- losing search ---')
    for line in w:
        print('  ', line)
