import sys
sys.path.insert(0, 'src')
from engine import Game

g = Game(seed=2)
for h in ('0101', '0611'):
    print(h, {d: (nb, g.model.travel_terrain(nb), g.place_kind(nb))
              for d, nb in g.model.neighbors(h).items()})
print('temples:', sorted(h for h, p in g.features['places'].items()
                         if p['kind'] == 'temple'))
