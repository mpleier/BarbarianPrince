"""How big is the party, and how fast does it actually move?

r204a: the party moves 1 hex/day on foot, 2 hexes/day if *every* living member
has a mount, 3 with winged mounts.  A single unmounted follower therefore
halves the whole party's speed, and r215/r217 charge food and lodging for every
follower.  This script measures how often the bot is mounted and how many
followers it is dragging around.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')

from engine import Game
from autoplay import Bot, TOTAL_DAYS

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

speed_sum = 0
speed_days = 0
party_sum = 0
party_days = 0
horse_days = 0
travel_days = 0
lost_days = 0
for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    orig = g.daily_menu

    def wrapped():
        global speed_sum, speed_days, party_sum, party_days
        speed_sum += g.speed()
        speed_days += 1
        party_sum += len(g.living())
        party_days += 1
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    horse_days += sum(1 for l in g.log if 'horses bought' in l.lower())
    travel_days += sum(1 for l in g.log if l.startswith('Travel action'))
    lost_days += sum(1 for l in g.log if '-> LOST' in l)

print(f'{N} campaigns {strategy}')
print(f'avg party size {party_sum / party_days:.2f}')
print(f'avg travel speed {speed_sum / speed_days:.2f} hexes/day')
print(f'horse purchases per campaign {horse_days / N:.2f}')
print(f'travel action days per campaign {travel_days / N:.1f}')
print(f'getting-lost events per campaign {lost_days / N:.1f}')
