"""Map geometry: distances between ruins (gold) and temples (the win)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game

g = Game(seed=1)
model = g.model
places = g.features['places']
ruins = sorted(h for h, p in places.items() if p['kind'] == 'ruins')
temples = sorted(h for h, p in places.items() if p['kind'] == 'temple')
towns = sorted(h for h, p in places.items() if p['kind'] in ('town', 'castle'))

print('ruins  ', ruins)
print('temples', temples)
print('towns  ', towns)
print()
for r in ruins:
    td = sorted((model.distance(r, t), t) for t in temples)
    nd = sorted((model.distance(r, t), t) for t in towns)
    print(f'ruin {r}: temples {td[:3]}  towns {nd[:3]}')
print()
for t in temples:
    rd = sorted((model.distance(t, r), r) for r in ruins)
    print(f'temple {t}: nearest ruins {rd[:3]}')
print()
print('start 0101 -> temples', sorted((model.distance('0101', t), t) for t in temples))
print('start 0101 -> ruins  ', sorted((model.distance('0101', r), r) for r in ruins))

