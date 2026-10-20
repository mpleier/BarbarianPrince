"""Measure the real per-day gold flow of the engine, by hex kind."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict
from engine import Game
from autoplay import Bot

orig_finish = Game.finish_day
flow = defaultdict(lambda: [0, 0])   # kind -> [days, gold delta]

def finish_day(self):
    kind = str(self.place_kind(self.hex))
    flow[kind][0] += 1
    flow[kind][1] += self.gold - getattr(self, '_gold_at_day_start', self.gold)
    return orig_finish(self)

Game.finish_day = finish_day

orig_menu = Game.daily_menu

def daily_menu(self):
    self._gold_at_day_start = self.gold
    return orig_menu(self)

Game.daily_menu = daily_menu

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
for s in range(1, N + 1):
    g = Game(seed=s)
    b = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=b.choose)

print(f'{N} games, strategy balanced')
for kind, (days, delta) in sorted(flow.items(), key=lambda x: -x[1][0]):
    print(f'  {kind:<8} days {days:>5}  net gold {delta:>7}  per day {delta/days:+.2f}')
