"""Per-day gold accounting keyed on the daily action prompt."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot
from collections import defaultdict

N = int(sys.argv[1]) if len(sys.argv) > 1 else 150

ruin_nets = []
temple_nets = []
other_nets = []
ruin_counts = defaultdict(int)

for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    marks = []

    def wrapped(prompt):
        i = bot.choose(prompt)
        title = prompt.get('title', '')
        if 'action in hex' in title.lower():
            marks.append((g.day, g.gold, g.place_kind(g.hex) or 'open'))
        return i

    g.run_until_idle(max_steps=6000, chooser=wrapped)
    marks.sort(key=lambda m: m[0])
    # dedupe by day, keep the first (start-of-day) gold
    seen = {}
    for d, gold, kind in marks:
        if d not in seen:
            seen[d] = (gold, kind)
    days = sorted(seen)
    for idx in range(len(days) - 1):
        d = days[idx]
        gold, kind = seen[d]
        nxt_gold = seen[days[idx + 1]][0]
        net = nxt_gold - gold
        if kind == 'ruins':
            ruin_nets.append(net)
        elif kind == 'temple':
            temple_nets.append(net)
        else:
            other_nets.append(net)

def avg(xs):
    return sum(xs) / len(xs) if xs else 0.0

def pctl(xs, p):
    xs = sorted(xs)
    return xs[int(len(xs) * p)] if xs else 0

print(f'games {N}')
print(f'ruin days  n={len(ruin_nets):5}  mean {avg(ruin_nets):+6.2f}  median {pctl(ruin_nets,0.5):+6.1f}')
print(f'temple days n={len(temple_nets):4}  mean {avg(temple_nets):+6.2f}  median {pctl(temple_nets,0.5):+6.1f}')
print(f'other days n={len(other_nets):5}  mean {avg(other_nets):+6.2f}')
print(f'gross ruin gold (only positive): {avg([x for x in ruin_nets if x > 0]):.2f}')
print(f'fraction of ruin days with 0 net: {sum(1 for x in ruin_nets if x == 0)/len(ruin_nets):.2f}')
