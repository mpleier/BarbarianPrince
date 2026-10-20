"""Win-rate harness: run the auto-play bot over many seeds and report stats."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 50

for strategy in ('cautious', 'balanced', 'aggressive'):
    wins = 0
    days = []
    golds = []
    peak_gold = []
    temple_days = 0
    reached_temple = 0
    reasons = {}
    for seed in range(1, N + 1):
        g = Game(seed=seed)
        bot = Bot(g, strategy)
        g.run_until_idle(max_steps=6000, chooser=bot.choose)
        if g.won:
            wins += 1
        days.append(g.day)
        golds.append(g.gold)
        peak_gold.append(getattr(g, 'peak_gold', g.gold))
        t = [h for h in g.visited if g.place_kind(h) == 'temple']
        temple_days += len(t)
        if t:
            reached_temple += 1
        reasons[g.reason or 'still playing'] = reasons.get(
            g.reason or 'still playing', 0) + 1
    print(f'{strategy:11} wins {wins}/{N}  avg days {sum(days)/len(days):.1f} '
          f'avg gold {sum(golds)/len(golds):.1f} peak gold {sum(peak_gold)/len(peak_gold):.1f}')
    print(f'    reached a temple: {reached_temple}/{N}  '
          f'temple hex-visits: {temple_days}')
    for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f'    {reason}: {count}')
