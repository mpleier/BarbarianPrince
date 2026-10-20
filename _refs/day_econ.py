"""Net gold per day, bucketed by the daily action actually taken.

Gold is snapshotted at the start of every day, so the delta across a day is the
true net of that day's action plus food and lodging (r215/r217).
"""
import re
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict
from engine import Game
from autoplay import Bot


class Tracked(Game):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.snapshots = []

    def note(self, text):
        m = re.match(r'Day (\d+) begins in hex (\d{4})', text)
        if m:
            self.snapshots.append((int(m.group(1)), self.gold, m.group(2)))
        self.log.append(text)


N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
buckets = defaultdict(list)
arrival_gold = []
overhead = []

for seed in range(1, N + 1):
    g = Tracked(seed=seed)
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    snaps = g.snapshots
    marks = [i for i, line in enumerate(g.log)
             if re.match(r'Day \d+ begins in hex \d{4}', line)]
    for i, (day, gold, hex_) in enumerate(snaps):
        window = g.log[marks[i] + 1: marks[i + 1] if i + 1 < len(marks) else len(g.log)]
        nxt = snaps[i + 1][1] if i + 1 < len(snaps) else g.gold
        act = 'other'
        for line in window:
            if line.startswith('Searching the ruins'):
                act = 'ruins'
            elif line.startswith('Offering of'):
                act = 'offering'
            elif line.startswith('Travel '):
                act = 'travel'
            elif line.startswith('Resting'):
                act = 'rest'
            elif line.startswith('News roll'):
                act = 'news'
            elif line.startswith('Audience'):
                act = 'audience'
        buckets[act].append(nxt - gold)
        if act == 'offering':
            meals = sum(int(m) for line in window
                        for m in re.findall(r'Bought meals for (\d+) gold', line))
            lodge = sum(int(m) for line in window
                        for m in re.findall(r'Paid (\d+) gold for lodging', line))
            offer = sum(int(m) for line in window
                        for m in re.findall(r'Offering of (\d+) gold', line))
            overhead.append((len(g.party), meals, lodge, offer))
    for day, gold, hex_ in snaps:
        if g.place_kind(hex_) == 'temple':
            arrival_gold.append((day, gold, len(g.party)))
            break

for name, rows in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
    n = len(rows)
    print(f'{name:<9} days {n:>5}  mean net gold {sum(rows)/n:>7.2f}  '
          f'zero-or-less {sum(1 for r in rows if r <= 0) / n:.2f}')

first = arrival_gold
print(f'\nfirst temple visit: mean day {sum(d for d, _, _ in first)/len(first):.1f}, '
      f'mean gold {sum(x[1] for x in first)/len(first):.1f}, '
      f'under 10 gold {sum(1 for _, x, _ in first if x < 10)/len(first):.2f}, '
      f'mean party {sum(p for _, _, p in first)/len(first):.2f}')

if overhead:
    n = len(overhead)
    print(f'\noffering days {n}: mean party {sum(p for p,_,_,_ in overhead)/n:.2f}, '
          f'meals {sum(m for _,m,_,_ in overhead)/n:.2f}, '
          f'lodging {sum(l for _,_,l,_ in overhead)/n:.2f}, '
          f'offering {sum(o for _,_,_,o in overhead)/n:.2f}')
