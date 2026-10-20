"""Measure the ACTUAL gold yield of every action the engine performs.

Walks the prompt stream directly so each chosen option can be paired with the
gold delta it produced.
"""
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

STATS = defaultdict(lambda: [0, 0])
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

wins = 0
for s in range(1, N + 1):
    g = Game(seed=s)
    bot = Bot(g, strategy)
    steps = 0
    while steps < 6000 and not g.game_over:
        g.advance()
        if not g.prompts or g.game_over:
            break
        prompt = g.current()
        title = prompt.get('title', '').lower()
        idx = bot.choose(prompt)
        label = prompt['options'][idx]['label']
        before = g.gold
        g.answer(idx)
        delta = g.gold - before
        if 'action in hex' in title:
            key = label.split('(')[-1].rstrip(')')
            STATS[key][0] += 1
            STATS[key][1] += delta
        steps += 1
    wins += 1 if g.won else 0

print(f'{N} games, strategy {strategy}, wins {wins}')
for k, (c, gold) in sorted(STATS.items(), key=lambda x: -x[1][1]):
    print(f'{k:12} count {c:6}  gold {gold:8}  avg {gold / max(1, c):7.2f}')
