import sys
sys.path.insert(0, 'src')
from engine import Game

g = Game(seed=2)
found = 0
for hid in sorted(g.model.grid):
    nbs = g.model.neighbors(hid)
    roads = [(d, nb) for d, nb in sorted(nbs.items()) if g.is_road_move(hid, nb)]
    if roads and len(nbs) > 1:
        print(hid, g.model.travel_terrain(hid),
              [(d, nb, g.model.travel_terrain(nb), g.is_road_move(hid, nb))
               for d, nb in sorted(nbs.items())])
        found += 1
        if found >= 5:
            break
