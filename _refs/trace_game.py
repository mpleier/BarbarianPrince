"""Diagnose the bot's daily action choices and gold trajectory."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 42
STRAT = sys.argv[2] if len(sys.argv) > 2 else 'balanced'
DAYS = int(sys.argv[3]) if len(sys.argv) > 3 else 75

g = Game(seed=SEED)
bot = Bot(g, STRAT)
for _ in range(DAYS * 6):
    if g.game_over:
        break
    prompt = g.advance()
    if prompt is None:
        break
    title = prompt.get('title', '')
    idx = bot.choose(prompt)
    if title.startswith('Day '):
        label = prompt['options'][idx]['label']
        print(f'day {g.day:3d} hex {g.hex} gold {g.gold:3d} food {g.food:2d} '
              f'party {len(g.living())} place {g.place_kind(g.hex)} -> {label}')
    g.answer(idx)

print('result:', g.reason, 'won', g.won, 'day', g.day, 'gold', g.gold)
print('temples visited:', [h for h in g.visited if g.place_kind(h) == 'temple'])
print('offering_bonus', g.offering_bonus)
