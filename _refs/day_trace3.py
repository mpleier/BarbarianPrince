"""Day-by-day trace with gold, modifiers and location for a given seed."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 11
g = Game(seed=seed)
bot = Bot(g, 'balanced')

last_day = 0
rows = []


def wrapped(prompt):
    i = bot.choose(prompt)
    label = prompt['options'][i]['label']
    title = prompt.get('title', '')
    if 'action in hex' in title.lower():
        rows.append((g.day, g.hex, g.place_kind(g.hex) or 'open', g.gold,
                     g.offering_bonus, g.omen_bonus, g.influence_bonus, label))
    return i


g.run_until_idle(max_steps=6000, chooser=wrapped)
print(f'seed {seed}: won={g.won} day={g.day} gold={g.gold}')
for r in rows:
    print(f'day {r[0]:3} {r[1]} {r[2]:8} gold {r[3]:4} '
          f'omns {r[4]}+{r[5]}+{r[6]} -> {r[7]}')
