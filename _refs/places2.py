import sys
sys.path.insert(0, 'src')
from collections import Counter
from engine import Game

g = Game(seed=1)
print(Counter(p['kind'] for p in g.features['places'].values()))
print('total hexes:', len(g.model.grid))
print('roads:', len(g.features['road_sides']))
print('rivers:', len(g.features['river_sides']))
for h, p in sorted(g.features['places'].items()):
    print(h, p['kind'], p['name'])
