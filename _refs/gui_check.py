"""Headless sanity check: build the GUI, render the map, count drawn hexes."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from gui import GameGUI

g = Game(seed=5)
app = GameGUI(g)
app.refresh_status()
print('canvas size %.1f x %.1f' % (app.map.w, app.map.h))
items = app.map.canvas.find_all()
print('canvas items:', len(items))
tags = {}
for it in items:
    for t in app.map.canvas.gettags(it):
        tags[t] = tags.get(t, 0) + 1
print('tags:', tags)
xs = [h['center'][0] for h in g.grid.values()]
ys = [h['center'][1] for h in g.grid.values()]
print('board extent: x %.1f..%.1f  y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)))
app.root.destroy()
print('GUI OK')
