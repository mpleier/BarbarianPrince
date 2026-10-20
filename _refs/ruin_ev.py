"""Exact expected gold of one r208 ruins search, resolved through the engine."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import random
from collections import Counter
from engine import Game
from autoplay import Bot

TRIALS = 20000
rng = random.Random(7)
RUINS = {int(k): v for k, v in Game().model.tables['ruins_search'].items()}
EVENTS = Game().model.events

def ev(code, depth=0):
    """Crude EV: gold only, die tables expanded."""
    e = EVENTS.get(code, {})
    text = e.get('text', '')
    total = 0.0
    # direct gold mentions
    import re
    for m in re.finditer(r'(\d+)\s+gold', text):
        pass
    return total

# Simulate with the engine instead.
g = Game(seed=1)
g.gold = 100000
g.hex = '0307'
b = Bot(g, 'balanced')
g.party = [c for c in g.party if c.prince]
golds = []
codes = Counter()
for _ in range(TRIALS):
    before = g.gold
    g.search_ruins()
    while g.prompts:
        p = g.prompts[-1]
        i = b.choose(p, record=False)
        g.prompts.pop()
        p['handler'](i) if 'handler' in p else None
    golds.append(before - g.gold)
    for l in g.log[-6:]:
        if l.startswith('Ruins roll'):
            codes[l.split('-> ')[1]] += 1
print('mean gold per ruins search:', sum(golds) / len(golds))
print('codes:', codes.most_common())
