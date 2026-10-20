"""Trace one campaign day-by-day to see where the days are wasted."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

for seed in (int(x) for x in sys.argv[1:]):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    rows = []

    def wrapped(prompt):
        i = bot.choose(prompt)
        title = prompt.get('title', '')
        if 'action in hex' in title.lower():
            rows.append((g.day, g.hex, g.place_kind(g.hex) or 'open',
                         g.gold, prompt['options'][i]['label']))
        return i

    g.run_until_idle(max_steps=6000, chooser=wrapped)
    print(f'=== seed {seed}  win={g.staff}  gold={g.gold} ===')
    for d, h, k, gold, label in rows:
        print(f'  day {d:>3} {h} {k:<7} gold {gold:>4}  {label}')
