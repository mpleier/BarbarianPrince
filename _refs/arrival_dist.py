"""Distribution of the state the bot arrives at the temple with.

The camp DP (_refs/camp_dp_exact.py) tells us P(win) for any (camp days, gold)
pair, so the only thing that matters macroscopically is the joint distribution
of those two numbers at the moment the party first reaches a temple.  This
prints that distribution, the DP value of each bucket and the realised win rate,
so the gap between plan and execution is visible.
"""
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '_refs')
sys.stdout.reconfigure(encoding='utf-8')

from collections import Counter
from engine import Game
from autoplay import Bot, TOTAL_DAYS
from camp_dp_exact import value as camp_value

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

rows = []
for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    state = {'arrival': None}
    orig = g.daily_menu

    def wrapped(state=state, g=g, orig=orig):
        if state['arrival'] is None and g.place_kind(g.hex) == 'temple':
            state['arrival'] = (g.day, g.gold)
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    arrival = state['arrival']
    days_at_temple = sum(1 for line in g.log if 'Offering of' in line)
    rows.append((arrival, g.staff, g.day, g.gold, days_at_temple,
                b.ruin_days))

wins = sum(1 for r in rows if r[1])
print(f'{N} campaigns {strategy}: win {wins / N:.3f}')
print(f'avg ruin-search days {sum(r[5] for r in rows) / N:.1f}')
print(f'avg offering days {sum(r[4] for r in rows) / N:.1f}')
print(f'avg arrival day {sum(r[0][0] for r in rows if r[0]) / N:.1f}')
print(f'avg gold at arrival {sum(r[0][1] for r in rows if r[0]) / N:.1f}')

buckets = Counter()
for arrival, won, day, gold, offers, ruins in rows:
    if arrival is None:
        buckets[(0, 0)] += 1
        continue
    d, gld = arrival
    camp = TOTAL_DAYS - d + 1
    gb = 0 if gld < 10 else 10 if gld < 30 else 30 if gld < 60 else 60 if gld < 100 else 100 if gld < 150 else 150 if gld < 200 else 200
    buckets[(camp, gb)] += 1

print('\ncamp days  gold bucket      n   DP P(win)')
for (camp, gb), n in sorted(buckets.items(), key=lambda x: -x[1])[:30]:
    if camp == 0:
        print(f'  {"never reached a temple":<32} {n:>3}   {"":>9}')
        continue
    print(f'  {camp:>9}d  {gb:>3}+ gold     {n:>3}   {camp_value(camp, gb, 0, 0, 0):>9.3f}')
