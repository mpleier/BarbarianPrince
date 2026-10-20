"""Measure the real per-day economics of ruin-farming and temple camping.

Runs many campaigns with the current bot and records, for every day, the
action taken and the gold change, so the DP can be fed measured numbers
instead of guesses.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 120

ruin_net = []          # gold change on a ruins-search day
temple_net = []        # gold change on a temple day (offering or otherwise)
first_temple_day = []
gold_at_temple = []
news_days = [0]

for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    st = {'gold': g.gold, 'day': g.day, 'kind': None, 'reached': None}

    def wrapped(prompt):
        i = bot.choose(prompt)
        title = prompt.get('title', '')
        if 'action in hex' in title.lower():
            label = prompt['options'][i]['label'].lower()
            kind = g.place_kind(g.hex) or 'open'
            day = g.day
            if day != st['day']:
                delta = g.gold - st['gold']
                if st['kind'] == 'ruins' and 'ruin' in label:
                    ruin_net.append(delta)
                elif st['kind'] == 'temple':
                    temple_net.append(delta)
                st['gold'] = g.gold
                st['day'] = day
                st['kind'] = kind
                if kind == 'temple' and st['reached'] is None:
                    st['reached'] = day
                    gold_at_temple.append(g.gold)
            if 'news' in label:
                news_days[0] += 1
        return i

    g.run_until_idle(max_steps=6000, chooser=wrapped)
    first_temple_day.append(st['reached'])


def avg(xs):
    return sum(xs) / len(xs) if xs else 0.0

print(f'games: {N}')
print(f'avg ruin-search net gold/day : {avg(ruin_net):+.2f}  (n={len(ruin_net)})')
print(f'avg temple-day net gold/day  : {avg(temple_net):+.2f}  (n={len(temple_net)})')
print(f'news actions per game        : {news_days[0] / N:.2f}')
print(f'games that reached a temple  : {sum(1 for x in first_temple_day if x)}/{N}')
print(f'avg first-temple day         : {avg([x for x in first_temple_day if x]):.1f}')
print(f'avg gold on arrival          : {avg(gold_at_temple):.1f}')
print(f'avg days remaining at arrival: {avg([70 - x for x in first_temple_day if x]):.1f}')
