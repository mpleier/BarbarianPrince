import sys
sys.path.insert(0, 'src')
from collections import deque
from engine import Game

g = Game(seed=42)
places = g.features['places']
temples = [h for h, p in places.items() if p['kind'] == 'temple']


def bfs(start):
    d = {start: 0}
    q = deque([start])
    while q:
        h = q.popleft()
        for nb in g.model.neighbors(h).values():
            if nb not in d:
                d[nb] = d[h] + 1
                q.append(nb)
    return d


for a in ['0101', '0701', '1311']:
    d = bfs(a)
    print(a, 'grid size', len(d),
          {t: d.get(t) for t in temples})
