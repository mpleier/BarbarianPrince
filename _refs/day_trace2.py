"""Trace one campaign day by day: hex, gold, action taken."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

g = Game(seed=seed)
bot = Bot(g, strategy)

daily_menu = g.daily_menu


def menu(prompt, record=True):
    idx = bot.choose(prompt, record)
    label = prompt['options'][idx]['label']
    if 'action in hex' in prompt.get('title', '').lower():
        print(f'day {g.day:3} hex {g.hex} gold {g.gold:4} '
              f'bonus {g.offering_bonus}+{g.omen_bonus}+{g.influence_bonus} '
              f'-> {label}')
    return idx


g.run_until_idle(max_steps=6000, chooser=menu)
print(f'\nwon={g.won} day={g.day} gold={g.gold} hex={g.hex}')
print('\n'.join(line for line in g.log if 'Offering of' in line))
