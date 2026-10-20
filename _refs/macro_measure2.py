"""Measure the macro structure of a bot campaign: where the days go."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200

first_temple_day = []
temple_days = []
ruin_days = []
gold_at_temple = []
action_counts = {}
wins = 0
win_days = []

for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    st = {'day': g.day, 'temple': 0, 'ruins': 0, 'reached': None}

    def wrapped(prompt):
        i = bot.choose(prompt)
        title = prompt.get('title', '')
        if 'action in hex' in title.lower():
            label = prompt['options'][i]['label']
            key = label.split('(')[-1].rstrip(')')
            action_counts[key] = action_counts.get(key, 0) + 1
            kind = g.place_kind(g.hex)
            if g.day != st['day']:
                st['day'] = g.day
                if kind == 'temple':
                    st['temple'] += 1
                    if st['reached'] is None:
                        st['reached'] = g.day
                        first_temple_day.append(g.day)
                        gold_at_temple.append(g.gold)
                elif kind == 'ruins':
                    st['ruins'] += 1
        return i

    g.run_until_idle(max_steps=6000, chooser=wrapped)
    temple_days.append(st['temple'])
    ruin_days.append(st['ruins'])
    if g.staff:
        wins += 1
        win_days.append(g.day)

def avg(xs):
    return sum(xs) / len(xs) if xs else 0.0

print(f'games {N}  wins {wins} ({100*wins/N:.1f}%)')
print(f'reached a temple: {len(first_temple_day)}/{N}')
print(f'avg first-temple day : {avg(first_temple_day):.1f}')
print(f'avg gold on arrival  : {avg(gold_at_temple):.1f}')
print(f'avg temple action days: {avg(temple_days):.1f}')
print(f'avg ruin action days  : {avg(ruin_days):.1f}')
if win_days:
    print(f'avg win day: {avg(win_days):.1f}')
print('daily actions taken:')
for k, v in sorted(action_counts.items(), key=lambda x: -x[1]):
    print(f'  {v:>5} {k}')
