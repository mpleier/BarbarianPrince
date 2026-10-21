import json, math, sys
sys.path.insert(0, 'src')
import river_trace as rt
from PIL import Image, ImageDraw

data = json.load(open('_refs/sides_traced.json', encoding='utf-8'))
def hx(s):
    return int(s[:2]), int(s[2:])

river = [tuple(map(hx, s)) for s in data['river_sides']]
roads = [tuple(map(hx, s)) for s in data['road_sides']]

board = rt.stitched()
W, H = board.size
d = ImageDraw.Draw(board)
for a, b in roads:
    e1, e2 = rt.shared_edge(a, b)
    d.line([e1, e2], fill=(255, 0, 0), width=10)
for a, b in river:
    e1, e2 = rt.shared_edge(a, b)
    d.line([e1, e2], fill=(0, 0, 255), width=12)

for i, (x0, y0, x1, y1) in enumerate([(0, 0, W//2, H//2), (W//2, 0, W, H//2),
                                     (0, H//2, W//2, H), (W//2, H//2, W, H)]):
    c = board.crop((x0, y0, x1, y1))
    c.thumbnail((700, 700))
    c.save('_refs/quad%d.png' % i)
print('ok')
