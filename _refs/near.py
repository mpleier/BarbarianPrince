import io
import json
import sys
from collections import deque

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

m = json.load(open('data/map.json', encoding='utf-8'))
H = {h['hex']: h for h in m['hexes']}
DIRS = {'N': (0, -1), 'NE': (1, 0), 'SE': (0, 1), 'SW': (-1, 1), 'NW': (-1, 0), 'S': (1, -1)}


def nbr(h, d):
    q, r = H[h]['q'], H[h]['r']
    a, b = DIRS[d]
    key = f'{q + a}{r + b}'
    return H.get(key)


def dist(a, b):
    seen = {a}
    dq = deque([(a, 0)])
    while dq:
        x, d = dq.popleft()
        if x == b:
            return d
        for dd in DIRS:
            q, r = H[x]['q'], H[x]['r']
            aa, bb = DIRS[dd]
            key = f'{q + aa}{r + bb}'
            if key in H and key not in seen:
                seen.add(key)
                dq.append((key, d + 1))
    return 99


ruins = [h for h in H if 'Ruins' in H[h]['terrain']]
temples = [h for h in H if 'Temple' in H[h]['terrain']]
towns = [h for h in H if 'Town' in H[h]['terrain']]

pairs = []
for ru in ruins:
    for t in temples:
        d = dist(ru, t)
        if d <= 3:
            pairs.append((d, ru, t))
pairs.sort()
print('ruin-temple pairs within 3 hexes:')
for d, ru, t in pairs[:30]:
    print(f'  {ru} ({H[ru]["terrain"]}) -> {t} ({H[t]["terrain"]}) : {d}')

print('\nruins with a town within 2 hexes:')
for ru in ruins:
    near = [t for t in towns if dist(ru, t) <= 2]
    if near:
        print(f'  {ru}: {near}')
