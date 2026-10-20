import io
import sys
from collections import deque

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'src')
from game_model import GameModel

m = GameModel.load()
grid = m.grid


def dist(a, b):
    seen = {a}
    dq = deque([(a, 0)])
    while dq:
        x, d = dq.popleft()
        if x == b:
            return d
        for n in grid[x]['neighbors']:
            if n not in seen:
                seen.add(n)
                dq.append((n, d + 1))
    return 99


ruins = [h for h in grid if 'Ruins' in grid[h]['terrain']]
temples = [h for h in grid if 'Temple' in grid[h]['terrain']]
towns = [h for h in grid if 'Town' in grid[h]['terrain']]

print('temples:', temples)
print('ruins:', ruins)
print('\nruin -> temple distances')
for ru in ruins:
    print(' ', ru, {t: dist(ru, t) for t in temples})

print('\nruins with a town within 2 hexes:')
for ru in ruins:
    near = [t for t in towns if dist(ru, t) <= 2]
    if near:
        print(f'  {ru}: {near}')
