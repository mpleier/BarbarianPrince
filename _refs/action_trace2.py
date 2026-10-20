"""Trace the daily actions of a handful of campaigns."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

seeds = [int(s) for s in sys.argv[1:]] or [1, 4, 5, 10]

for seed in seeds:
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    actions = []
    chooser = bot.choose

    def wrapped(prompt):
        i = chooser(prompt)
        title = prompt.get('title', '')
        if 'action in hex' in title.lower():
            actions.append((g.day, g.hex, prompt['options'][i]['label'], g.gold))
        return i

    g.run_until_idle(max_steps=6000, chooser=wrapped)
    print(f'=== seed {seed}: gold {g.gold} won {g.won} ===')
    for d, h, a, gold in actions:
        print(f'  day {d:3} hex {h} {a:30} gold {gold}')
    print()
