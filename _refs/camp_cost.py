"""Per-day gold/hex audit: how much a temple camp day really costs."""
import sys, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

orig = Game.finish_day
snap = []

def wrapped(self):
    snap.append((self.day, self.hex, self.gold, len(self.living())))
    return orig(self)

Game.finish_day = wrapped

N = 200
temple_day_cost = collections.Counter()
ruin_day_cost = collections.Counter()
for s in range(1, N + 1):
    g = Game(seed=s)
    b = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    for i in range(1, len(snap)):
        if snap[i - 1][1] == snap[i][1]:
            d = snap[i][1]
            kind = g.place_kind(d)
            delta = snap[i][2] - snap[i - 1][2]
            if kind == 'temple':
                temple_day_cost[delta] += 1
            elif kind == 'ruins':
                ruin_day_cost[delta] += 1
    snap.clear()

print('temple day gold deltas (party of 1):')
tot = sum(temple_day_cost.values())
for k, v in sorted(temple_day_cost.items()):
    print(f'  {k:>5}: {v} ({v/max(1,tot):.1%})')
print('mean temple day delta:', sum(k*v for k,v in temple_day_cost.items())/max(1,tot))
tot2 = sum(ruin_day_cost.values())
print('ruin day mean delta:', sum(k*v for k,v in ruin_day_cost.items())/max(1,tot2))
