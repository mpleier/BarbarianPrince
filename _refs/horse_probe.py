"""How often does a horse actually become available, and does the bot buy it?

r210 hiring in a town or castle rolls 5 (horses at 10 gold) or 10 (horses at
7 gold).  A mounted party moves 2 hexes/day (r204a), which halves the ~23 days
the campaign currently spends walking.  This counts the opportunities and what
the bot did with them.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')

from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

opp = 0
bought = 0
games_with_opp = 0
games_bought = 0
first_day = []
for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    seen = []
    orig_choose = b.choose

    def traced(prompt):
        idx = orig_choose(prompt)
        title = prompt.get('title', '').lower()
        if 'horse' in title:
            for i, o in enumerate(prompt['options']):
                if 'Buy' in o['label']:
                    seen.append((g.day, g.gold, o['label'], idx == i))
                    break
        return idx
    b.choose = traced
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    if seen:
        games_with_opp += 1
        opp += len(seen)
        if any(s[3] for s in seen):
            games_bought += 1
            first_day.append(min(s[0] for s in seen if s[3]))

print(f'{N} campaigns {strategy}')
print(f'horse offers seen: {opp} ({games_with_opp} campaigns had one)')
print(f'campaigns that bought a horse: {games_bought}')
if first_day:
    print(f'avg day of first purchase {sum(first_day) / len(first_day):.1f}')
