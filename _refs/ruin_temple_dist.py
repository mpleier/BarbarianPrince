"""Which ruin is closest to which temple, and how fast can the party move?"""
import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot


def bfs(grid, neighbors, start):
    d = {start: 0}
    q = deque([start])
    while q:
        h = q.popleft()
        for nb in neighbors(h).values():
            if nb not in d:
                d[nb] = d[h] + 1
                q.append(nb)
    return d


g = Game(seed=1)
places = g.features['places']
ruins = [h for h, p in places.items() if p['kind'] == 'ruins']
temples = [h for h, p in places.items() if p['kind'] == 'temple']
for r in ruins:
    d = bfs(g.model.grid, g.model.neighbors, r)
    print('ruin %s -> %s' % (r, sorted((d.get(t, 999), t) for t in temples)))
print('start hex', g.hex, 'speed on foot', g.speed())
