"""Audit the stitched scan against the hex grid.

Checks:
  1. coverage  - does the stitched image cover every hex centre?
  2. alignment - is the artwork colour under each hex centre closest to the
                 colour of the terrain the model assigns to that hex?
  3. geometry  - how far the scan rect and the board bounds disagree.

The terrain colours are learned from the scan itself (the median colour of
each terrain class), so this is a self-consistency test: if the lattice were
shifted or stretched, hexes would systematically land in the wrong colour
class and the agreement rate would collapse.

Run:  python _refs/scan_audit.py
"""
import sys
sys.path.insert(0, 'src')

from collections import defaultdict
from statistics import median

from PIL import Image

from game_model import GameModel
from geometry import NC, NR, R, DY, board_bounds, board_xy
from map_scan import scan_rect, stitch


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def grid_line_test(img, rect):
    """Do the predicted flat hex edges land on the printed white grid lines?

    For every hex, sample the midpoint of its top and bottom flat edge and
    compare the brightness there with the same point nudged 8 px sideways.
    A correct lattice puts the samples on the printed line, so the edge
    sample is consistently brighter than the control.
    """
    sx, sy, sw, sh = rect
    scale = img.size[0] / sw

    def bright(x, y):
        u = min(max(int(round((x - sx) * scale)), 0), img.size[0] - 1)
        v = min(max(int(round((y - sy) * scale)), 0), img.size[1] - 1)
        p = img.getpixel((u, v))
        return (p[0] + p[1] + p[2]) / 3.0

    on_edge = off_edge = 0
    wins = 0
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            cx, cy = board_xy(col, row)
            for sign in (-1, 1):
                y = cy + sign * DY / 2.0
                e = bright(cx, y)
                c = max(bright(cx + 8, y + 8), bright(cx - 8, y - 8))
                on_edge += e
                off_edge += c
                wins += e > c
    n = 2 * NC * NR
    print(f'\nprinted grid lines: edge sample brighter than control in '
          f'{wins}/{n} hexes ({100 * wins / n:.1f}%)')
    print(f'  mean brightness on the line {on_edge / n:.1f} vs off it {off_edge / n:.1f}')


def main():
    model = GameModel.load()
    rect = scan_rect()
    img = stitch(width=1800)
    sx, sy, sw, sh = rect
    scale = img.size[0] / sw
    minx, miny, maxx, maxy = board_bounds()

    print('scan rect      :', rect, ' cached image:', img.size)
    print('board bounds   :', tuple(round(v, 1) for v in board_bounds()))
    print('scan covers    : x %.1f..%.1f  y %.1f..%.1f' % (sx, sx + sw, sy, sy + sh))
    print('board needs    : x %.1f..%.1f  y %.1f..%.1f' % (minx, maxx, miny, maxy))
    print('shortfall      : left %.1f  top %.1f  right %.1f  bottom %.1f'
          % (minx - sx, miny - sy, (sx + sw) - maxx, (sy + sh) - maxy))

    samples = {}
    outside = []
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            hid = f'{col:02d}{row:02d}'
            cx, cy = board_xy(col, row)
            px, py = (cx - sx) * scale, (cy - sy) * scale
            if not (0 <= px < img.size[0] and 0 <= py < img.size[1]):
                outside.append(hid)
                continue
            pts = []
            for dx, dy in ((0, 0), (R * 0.3, 0), (-R * 0.3, 0), (0, R * 0.3), (0, -R * 0.3)):
                u = min(max(int(round((cx + dx - sx) * scale)), 0), img.size[0] - 1)
                v = min(max(int(round((cy + dy - sy) * scale)), 0), img.size[1] - 1)
                pts.append(img.getpixel((u, v)))
            avg = tuple(round(sum(p[i] for p in pts) / len(pts)) for i in range(3))
            samples[hid] = (model.grid[hid]['terrain'], avg)

    print('hex centres outside the scan:', len(outside), outside[:20])
    grid_line_test(img, rect)

    by_terrain = defaultdict(list)
    for h, (t, c) in samples.items():
        by_terrain[t].append(c)
    centre_of = {t: tuple(round(median(c[i] for c in cs)) for i in range(3))
                 for t, cs in by_terrain.items()}

    print('\nmedian artwork colour per terrain (learned from the scan)')
    for t, c in sorted(centre_of.items()):
        print(f'  {t:12s} rgb{c}  ({len(by_terrain[t])} hexes)')

    print('\nnearest-median classification of every hex centre')
    agree = 0
    confusion = defaultdict(int)
    for h, (t, c) in samples.items():
        guess = min(centre_of, key=lambda k: dist(centre_of[k], c))
        if guess == t:
            agree += 1
        else:
            confusion[(t, guess)] += 1
    print(f'  {agree} / {len(samples)} hexes classified correctly '
          f'({100 * agree / len(samples):.1f}%)')
    for (t, g), n in sorted(confusion.items(), key=lambda kv: -kv[1])[:10]:
        print(f'  confused {t} -> {g}: {n}')

    print('\nmatch rate by board row (drift would show as a gradient):')
    for row in range(1, NR + 1):
        rows = [h for h in samples if int(h[2:]) == row]
        ok = sum(1 for h in rows
                 if min(centre_of, key=lambda k: dist(centre_of[k], samples[h][1]))
                 == samples[h][0])
        print(f'  row {row:2d}  {ok:2d}/{len(rows):2d}  ' + '#' * round(30 * ok / max(1, len(rows))))


if __name__ == '__main__':
    main()
