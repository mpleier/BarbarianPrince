"""Classify every campaign that never makes an r212 offering.

Three failure modes matter for the macro plan:
  never  - the party never walks into a temple at all
  short  - it passes through a temple and leaves
  camped - it parks at a temple but is too broke to offer
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300


import re

def day_hexes(g):
    """(day, hex) pairs reconstructed from the campaign log."""
    days = []
    for line in g.log:
        m = re.match(r'Day (\d+) begins in hex (\d{4})', line)
        if m:
            days.append((int(m.group(1)), m.group(2)))
    return days


never, short, camped = [], [], []
for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    try:
        g.run_until_idle(max_steps=6000, chooser=bot.choose)
    except Exception as exc:
        print(f'seed {seed} crashed: {exc}')
        continue
    if any(l.startswith('Offering of') for l in g.log):
        continue
    tdays = [d for d, h in day_hexes(g) if g.place_kind(h) == 'temple']
    if not tdays:
        never.append((seed, g.day, g.gold, g.hex))
    elif len(tdays) <= 2:
        short.append((seed, g.day, g.gold, g.hex, len(tdays)))
    else:
        camped.append((seed, g.day, g.gold, g.hex, len(tdays)))

print(f'never reached a temple : {len(never)}')
print(f'passed straight through: {len(short)}')
print(f'camped but never offered: {len(camped)}')
for label, rows in (('never', never), ('short', short), ('camped', camped)):
    for r in rows[:12]:
        print(f'  {label:<6} seed {r[0]:>3}  day {r[1]:>2}  gold {r[2]:>4}  '
              f'hex {r[3]}  temple days {r[4] if len(r) > 4 else 0}')
