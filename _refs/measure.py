"""Measure the true distribution of ruin-search payouts and travel times."""
import sys, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

orig = Game.search_ruins
payouts = []

def wrapped(self):
    before = self.gold
    out = orig(self)
    payouts.append(self.gold - before)
    return out

Game.search_ruins = wrapped

N = 400
travel_steps = 0
lost_days = 0
road_steps = 0
days_per_game = []

for s in range(1, N + 1):
    g = Game(seed=s)
    b = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    days_per_game.append(g.day)
    for line in g.log:
        if line.startswith('Travel '):
            travel_steps += 1
            if '[road]' in line:
                road_steps += 1
        if '-> LOST' in line:
            lost_days += 1

c = collections.Counter(payouts)
n = len(payouts)
print(f'ruin search days: {n}')
print(f'mean payout: {sum(payouts)/n:.2f}  median: {sorted(payouts)[n//2]}')
buckets = collections.Counter()
for p in payouts:
    if p <= 0:
        buckets['<=0'] += 1
    elif p < 50:
        buckets['1-49'] += 1
    elif p < 100:
        buckets['50-99'] += 1
    elif p < 200:
        buckets['100-199'] += 1
    elif p < 500:
        buckets['200-499'] += 1
    else:
        buckets['500+'] += 1
for k, v in buckets.items():
    print(f'  {k}: {v} ({v/n:.1%})')
print(f'travel attempts {travel_steps}, lost {lost_days} ({lost_days/max(1,travel_steps):.1%}), road {road_steps}')
print(f'avg game days {sum(days_per_game)/len(days_per_game):.1f}')

