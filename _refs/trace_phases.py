"""Summarise the phase structure of N campaigns: ruin days, travel days, camp days."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
strategy = sys.argv[2] if len(sys.argv) > 2 else 'cautious'

tot = {'ruin': 0, 'temple': 0, 'travel': 0, 'town': 0, 'other': 0}
wins = 0
first_temple = []
camp_len = []
for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, strategy)
    kinds = []

    def wrapped(prompt):
        i = bot.choose(prompt)
        title = prompt.get('title', '').lower()
        if 'action in hex' in title:
            kinds.append(g.place_kind(g.hex) or 'open')
        return i

    g.run_until_idle(max_steps=6000, chooser=wrapped)
    if g.staff:
        wins += 1
    for k in kinds:
        if k == 'ruins':
            tot['ruin'] += 1
        elif k == 'temple':
            tot['temple'] += 1
        elif k == 'open':
            tot['travel'] += 1
        elif k in ('town', 'castle', 'camp', 'marsh', 'pass'):
            tot['town'] += 1
        else:
            tot['other'] += 1
    if 'temple' in kinds:
        first_temple.append(kinds.index('temple'))
        camp_len.append(len(kinds) - kinds.index('temple'))

print(f'seeds {N}  wins {wins} ({wins / N:.3f})')
for k, v in tot.items():
    print(f'  {k:<8} {v / N:6.1f} days/game')
print(f'  first temple action at day {sum(first_temple) / len(first_temple):.1f}')
print(f'  days from first temple to end: {sum(camp_len) / len(camp_len):.1f}')
