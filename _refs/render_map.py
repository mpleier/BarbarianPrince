"""Render the reconstructed board (terrain, roads, rivers, places) to a PNG
so the geometry and feature detection can be eyeballed.

    python _refs/render_map.py [out.png]
"""
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from PIL import Image, ImageDraw

from geometry import NC, NR, R
from game_model import GameModel
from features import load_features

SCALE = 0.30


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'data/board_preview.png'
    model = GameModel.load()
    feats = load_features()
    grid = model.grid
    colours = feats['terrain_colors']

    xs = [h['center'][0] for h in grid.values()]
    ys = [h['center'][1] for h in grid.values()]
    minx, maxx = min(xs) - R, max(xs) + R
    miny, maxy = min(ys) - R, max(ys) + R
    W = int((maxx - minx) * SCALE) + 20
    H = int((maxy - miny) * SCALE) + 20
    img = Image.new('RGB', (W, H), '#f4f1e8')
    d = ImageDraw.Draw(img)

    def px(x, y):
        return ((x - minx) * SCALE + 10, (y - miny) * SCALE + 10)

    def hex_pts(h):
        cx, cy = px(*h['center'])
        return [(cx + SCALE * R * math.cos(math.radians(a)),
                 cy + SCALE * R * math.sin(math.radians(a)))
                for a in range(0, 360, 60)]

    for h in grid.values():
        d.polygon(hex_pts(h), fill=colours.get(h['terrain'], '#d8d8d8'),
                  outline='#555')

    def shared_edge(a, b):
        ha, hb = grid[a], grid[b]
        vx, vy = hb['center'][0] - ha['center'][0], hb['center'][1] - ha['center'][1]
        n = math.hypot(vx, vy)
        nx, ny = -vy / n * R / 2, vx / n * R / 2
        mx, my = (ha['center'][0] + hb['center'][0]) / 2, (ha['center'][1] + hb['center'][1]) / 2
        return [px(mx + nx, my + ny), px(mx - nx, my - ny)]

    for a, b in feats['river_sides']:
        d.line(shared_edge(a, b), fill='#2b6fb5', width=4)

    for a, b in feats['road_sides']:
        d.line(shared_edge(a, b), fill='#8a5a2b', width=4)

    for hid, place in feats['places'].items():
        cx, cy = px(*grid[hid]['center'])
        d.text((cx - 12, cy - 10), place['name'], fill='#7a2f2f')

    d.text((10, 2), 'Reconstructed board: terrain / roads (brown) / rivers (blue)',
           fill='#333')
    img.save(out)
    print('wrote', out, img.size)


if __name__ == '__main__':
    main()
