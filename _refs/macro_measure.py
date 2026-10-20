"""Measure the macro structure of a bot campaign: where the days go."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot
from collections import Counter

N = 200
first_temple_day = []
temple_days = []
ruin_days = []
gold_at_temple = []
win_days = []
reached_temple = 0
wins = 0

for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    steps = 0
    seen_temple = False
    t_days = 0
    r_days = 0
    while not g.game_over and steps < 6000:
        p = g.current()
        if not p:
            break
        i = bot.choose(p)
        label = p['options'][i]['label']
        kind = g.place_kind(g.hex)
        if 'action in hex' in p['title'].lower():
            if kind == 'temple':
                t_days += 1
                if not seen_temple:
                    seen_temple = True
                    first_temple_day.append(g.day)
                    gold_at_temple.append(g.gold)
            elif kind == 'ruins':
                r_days += 1
        g.answer(i)
        steps += 1
    temple_days.append(t_days)
    ruin_days.append(r_days)
    if g.staff:
        wins += 1
        win_days.append(g.day)

print(f'games {N}  wins {wins} ({100*wins/N:.1f}%)')
print(f'reached a temple: {len(first_temple_day)}/{N}')
print(f'avg first-temple day: {sum(first_temple_day)/max(1,len(first_temple_day)):.1f}')
print(f'avg gold on arrival:  {sum(gold_at_temple)/max(1,len(gold_at_temple)):.1f}')
print(f'avg temple action days: {sum(temple_days)/N:.1f}')
print(f'avg ruin action days:   {sum(ruin_days)/N:.1f}')
if win_days:
    print(f'avg win day: {sum(win_days)/len(win_days):.1f}')
