"""Dump the daily action the bot actually picks, grouped by place kind.

`phase_audit2` shows ~11 days a campaign are spent standing on a temple hex
without making an offering.  This script records the exact label of the action
chosen on every day so those days can be attributed to a specific rule.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')

from collections import Counter
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

by_place = Counter()
labels = Counter()
for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    orig = g.daily_menu

    def wrapped():
        orig()
        p = g.current()
        if p and 'action in hex' in p.get('title', '').lower():
            i = b.suggest(p)
            lab = p['options'][i]['label']
            key = lab.split('(')[0].strip().lower()
            labels[key] += 1
            by_place[(g.place_kind(g.hex), key)] += 1
        return None
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)

print(f'{N} campaigns {strategy}: daily action chosen per day')
for k, v in labels.most_common():
    print(f'  {k:<28} {v / N:6.2f}')
print('\nby place:')
for (place, act), v in sorted(by_place.items(), key=lambda x: -x[1])[:25]:
    print(f'  {place:<8} {act:<28} {v / N:6.2f}')
