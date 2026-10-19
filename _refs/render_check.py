"""Render the web UI's map to a PNG so the geometry can be eyeballed.

    python _refs/render_check.py
"""
import math
import sys

sys.path.insert(0, 'src')
from PIL import Image, ImageDraw

from geometry import NC, NR, R, board_bounds, board_corners, board_xy, hex_id
from features import load_features
from game_model import GameModel

SCALE = 0.24
MODEL = GameModel.load()
FEATS = load_features()

COLORS = FEATS['terrain_colors']
SYMBOL = {'town': 'o', 'village': 'o', 'city': 'O', 'castle': '*', 'fort': '*',
          'tower': '*', 'temple': '+', 'shrine': '+', 'ruins': 'x', 'mine': '#',
          'farm': 'f', 'hollow': 'o', 'pool': '~', 'inn': 'i', 'cave': 'c',
          'camp': 'c', 'pass': '^', 'marsh': '~'}


def edge(a, b, centres):
    ha, hb = centres[a], centres[b]
    vx, vy = hb[0] - ha[0], hb[1] - ha[1]
    n = math.hypot(vx, vy) or 1
    nx, ny = -vy / n * R / 2, vx / n * R / 2
    mx, my = (ha[0] + hb[0]) / 2, (ha[1] + hb[1]) / 2
    return [(mx + nx) * SCALE, (my + ny) * SCALE, (mx - nx) * SCALE, (my - ny) * SCALE]


def main():
    minx, miny, maxx, maxy = board_bounds()
    img = Image.new('RGB', (int((maxx - minx) * SCALE), int((maxy - miny) * SCALE)), '#fbf7ee')
    d = ImageDraw.Draw(img)
    centres = {}
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            hid = hex_id(col, row)
            cx, cy = board_xy(col, row)
            centres[hid] = (cx, cy)
            pts = [((x - minx) * SCALE, (y - miny) * SCALE)
                   for x, y in board_corners(col, row)]
            d.polygon(pts, fill=COLORS.get(MODEL.grid[hid]['terrain'], '#d8d8d8'),
                      outline='#6b6355')

    for a, b in FEATS['river_sides']:
        x1, y1, x2, y2 = edge(a, b, centres)
        d.line([(x1 - minx * SCALE, y1 - miny * SCALE),
               (x2 - minx * SCALE, y2 - miny * SCALE)], fill='#2b7bb0', width=3)
    for a, b in FEATS['road_sides']:
        x1, y1, x2, y2 = edge(a, b, centres)
        d.line([(x1 - minx * SCALE, y1 - miny * SCALE),
               (x2 - minx * SCALE, y2 - miny * SCALE)], fill='#7a5c34', width=3)

    for hid, p in FEATS['places'].items():
        cx, cy = centres[hid]
        d.text(((cx - minx) * SCALE - 4, (cy - miny) * SCALE - 8),
               SYMBOL.get(p['kind'], '*'), fill='#222')

    d.ellipse((centres['0101'][0] * SCALE - minx * SCALE - 20,
               centres['0101'][1] * SCALE - miny * SCALE - 20,
               centres['0101'][0] * SCALE - minx * SCALE + 20,
               centres['0101'][1] * SCALE - miny * SCALE + 20), fill='#8b3a2e')
    img.save('_refs/web_board_check.png')
    print('wrote _refs/web_board_check.png', img.size)


if __name__ == '__main__':
    main()
