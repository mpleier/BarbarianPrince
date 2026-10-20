"""Exact distribution of the net gold from one r208 ruins search.

Each trial starts from a fresh campaign so the party state (and the e132
"organised search" re-roll) is realistic: the Prince alone, 1000 gold banked
so food and lodging never interfere.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
from engine import Game
from autoplay import Bot

TRIALS = 20000
outcomes = Counter()
for _ in range(TRIALS):
    g = Game(seed=_)
    g.gold = 1000
    g.hex = '0307'
    g.party = [c for c in g.party if c.prince]
    b = Bot(g, 'balanced')
    before = g.gold
    g.search_ruins()
    while g.prompts:
        p = g.prompts.pop()
        handler = p.get('handler')
        if handler:
            handler(b.choose(p, record=False))
    outcomes[g.gold - before] += 1

total = sum(outcomes.values())
print(f'{total} ruin searches')
for gold, n in sorted(outcomes.items()):
    print(f'  {gold:>6} gold  {n/total*100:6.2f}%')
mean = sum(g * n for g, n in outcomes.items()) / total
print(f'mean {mean:.3f} gold per ruin day')
