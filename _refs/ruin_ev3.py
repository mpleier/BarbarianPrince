"""Exact expected net gold of one r208 ruins search, resolved through the engine.

The party is the Prince alone (skill 8), so the search bonus is always +1 and
the roll distribution is dice+1 -> 3..13 (capped at 12).
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import random
from collections import Counter
from engine import Game
from autoplay import Bot

TRIALS = 30000
rng = random.Random(11)

template = Game(seed=1)
BOT = Bot(template, 'balanced')

golds = []
codes = Counter()
outcomes = Counter()

for t in range(TRIALS):
    g = Game(seed=rng.randrange(10 ** 9))
    g.gold = 500
    g.hex = '0307'
    g.party = [c for c in g.party if c.prince]
    before = g.gold
    g.search_ruins()
    steps = 0
    while g.prompts and steps < 60:
        p = g.prompts.pop(0)
        if g.combat:
            break
        idx = BOT.choose(p, record=False)
        p['options'][idx]['handler']()
        steps += 1
    golds.append(g.gold - before)
    for line in g.log:
        if line.startswith('Ruins roll'):
            codes[line.split('-> ')[1]] += 1
    outcomes[gold - before if False else g.gold - before] += 1

mean = sum(golds) / len(golds)
print('trials', len(golds), 'mean net gold per search: %.2f' % mean)
print('median', sorted(golds)[len(golds) // 2])
print('negative outcomes:', sum(1 for x in golds if x < 0), 'zero:', sum(1 for x in golds if x == 0))
print('codes:', codes.most_common())
