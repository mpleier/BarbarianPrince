"""Track the gold balance at the end of every day, and the action taken.

Writes UTF-8 to _refs/goldflow_<seed>.txt so PowerShell redirection cannot
mangle the output.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 2
out = os.path.join(os.path.dirname(__file__), f'goldflow_{seed}.txt')

g = Game(seed=seed)
bot = Bot(g, 'balanced')

day_actions = {}
gold_at_day = {}
hex_at_day = {}


def chooser(prompt):
    i = bot.choose(prompt)
    title = prompt.get('title', '').lower()
    label = prompt['options'][i]['label']
    if 'action in hex' in title:
        day_actions[g.day] = label
        gold_at_day[g.day] = g.gold
        hex_at_day[g.day] = g.hex
    return i


g.run_until_idle(max_steps=6000, chooser=chooser)

lines = [f'seed {seed}: won={g.won} day={g.day} gold={g.gold} '
         f'offering_bonus={g.offering_bonus} staff={g.staff}']
lines.append(f'hexes visited: {len(g.visited)}')
lines.append(f'temples visited: {[h for h in g.visited if g.place_kind(h) == "temple"]}')
lines.append('')
for d in sorted(gold_at_day):
    lines.append(f'day {d:3}  hex {hex_at_day[d]}  {str(g.place_kind(hex_at_day[d])):8}  '
                 f'gold {gold_at_day[d]:5}  -> {day_actions[d]}')
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('wrote', out)
print('\n'.join(lines[:40]))
