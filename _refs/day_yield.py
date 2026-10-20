"""Measure the true net gold per day for each kind of day the bot actually has."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter, defaultdict
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

buckets = defaultdict(lambda: [0, 0])   # label -> [days, gold]

for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    marks = []
    orig = g.daily_menu

    def wrapped():
        marks.append((g.day, g.hex, g.place_kind(g.hex), g.gold, len(g.log)))
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    marks.append((g.day, g.hex, g.place_kind(g.hex), g.gold, len(g.log)))
    for i in range(len(marks) - 1):
        day, hex_, kind, gold, log_at = marks[i]
        nxt = marks[i + 1]
        window = g.log[log_at:nxt[4]]
        if any(l.startswith('Searching the ruins') for l in window):
            label = 'ruin'
        elif any(l.startswith('Offering of') for l in window):
            label = 'temple-offer'
        elif any(l.startswith('Seeking news') for l in window):
            label = 'news'
        elif any(l.startswith('Travel action') for l in window):
            label = 'travel'
        elif any(l.startswith('Resting') for l in window):
            label = 'rest'
        else:
            label = 'other'
        buckets[label][0] += 1
        buckets[label][1] += nxt[3] - gold

for label, (days, gold) in sorted(buckets.items(), key=lambda kv: -kv[1][0]):
    print(f'{label:<14} days {days:>5}  net gold {gold:>7}  per day {gold / days:>6.2f}')
