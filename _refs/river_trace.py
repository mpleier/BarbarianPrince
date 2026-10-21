"""Trace the rivers and roads as polylines of hex-sides on the stitched board.

Method
------
1. stitch map1.jpg + map2.jpg into one unified-frame image (geometry.BOARD_Y_OFF)
   so that every hex - including the ones straddling the row 12/13 seam - is
   sampled in a single coordinate system.
2. for every adjacent hex pair, sample the *shared edge* itself (not the
   centre-to-centre line) for blue (river) and road-coloured pixels.
3. join two river sides only when they meet at a grid vertex that is itself
   wet.  This is far more reliable than dilating the whole blue mask and
   labelling components: dilation merges every river that merely comes close
   to another one, which is why the old version produced one 32-side blob.
4. walk each component into an ordered chain, report its endpoints and write
   an overlay image for visual verification.

Outputs: _refs/sides_traced.json, _refs/sides_traced_overlay.png
"""
import json
import math
import os
import sys
from collections import defaultdict

from PIL import Image, ImageDraw
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, NR, R, BOARD_Y_OFF, board_xy, neighbours

MAPS = ['map1.jpg', 'map2.jpg']
RIVER_FRAC = 0.50
ROAD_FRAC = 0.50
WET_FRAC = 0.15      # blue fraction inside the 12 px disc at a grid vertex
WET_RADIUS = 12
VERTEX_TOL = 4       # px: two corner points this close are the same vertex


def stitched():
    """Paste both scans into one unified-frame board image."""
    im1 = Image.open('_refs/map1.jpg').convert('RGB')
    im2 = Image.open('_refs/map2.jpg').convert('RGB')
    W = max(im1.width, im2.width)
    H = int(max(im1.height + BOARD_Y_OFF['map1.jpg'],
                im2.height + BOARD_Y_OFF['map2.jpg'])) + 20
    board = Image.new('RGB', (W, H), (255, 255, 255))
    for name, img in (('map1.jpg', im1), ('map2.jpg', im2)):
        board.paste(img, (0, int(round(BOARD_Y_OFF[name]))))
    return board


def masks(board):
    """River = saturated cyan/teal band (HSV hue ~176-233 deg, S >= 24%).
    The naive "bb > rr" test also fires on the blue-grey mountain shading,
    which produced ~25 phantom 'rivers' in the highlands."""
    a = np.array(board).astype(np.int32)
    rr, gg, bb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    hsv = np.array(board.convert('HSV')).astype(np.int32)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    blue = (H >= 125) & (H <= 165) & (S >= 60) & (V >= 90)
    road = (rr > 115) & (rr - gg > 22) & (rr - bb > 18) & (gg < 175) & (bb < 165)
    return blue, road


def shared_edge(a, b):
    """The two endpoints of the hex-side shared by hexes a and b."""
    p1, p2 = board_xy(*a), board_xy(*b)
    mx, my = (p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0
    vx, vy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(vx, vy)
    px, py = -vy / n, vx / n
    return (mx + px * R / 2, my + py * R / 2), (mx - px * R / 2, my - py * R / 2)


def frac(mask, x, y, rad=1):
    H, W = mask.shape
    hits = tot = 0
    for dx in range(-rad, rad + 1):
        for dy in range(-rad, rad + 1):
            sx, sy = int(x + dx), int(y + dy)
            if 0 <= sx < W and 0 <= sy < H:
                tot += 1
                hits += mask[sy, sx]
    return hits / max(tot, 1)


def disc_frac(mask, x, y, rad):
    H, W = mask.shape
    hits = tot = 0
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            if dx * dx + dy * dy <= rad * rad:
                sx, sy = int(x + dx), int(y + dy)
                if 0 <= sx < W and 0 <= sy < H:
                    tot += 1
                    hits += mask[sy, sx]
    return hits / max(tot, 1)


def scan_sides(blue, road):
    """Sample every hex-side: returns {(hexA, hexB): (blue_frac, road_frac)}."""
    scores = {}
    for c in range(1, NC + 1):
        for r in range(1, NR + 1):
            for hid in neighbours(c, r).values():
                nc, nr = int(hid[:2]), int(hid[2:])
                key = tuple(sorted(((c, r), (nc, nr))))
                if key in scores:
                    continue
                e1, e2 = shared_edge((c, r), (nc, nr))
                ang = math.atan2(e2[1] - e1[1], e2[0] - e1[0]) + math.pi / 2
                ca, sa = math.cos(ang), math.sin(ang)
                bt = rt = tot = 0
                for t in np.linspace(0.05, 0.95, 40):
                    bx = e1[0] + (e2[0] - e1[0]) * t
                    by = e1[1] + (e2[1] - e1[1]) * t
                    for off in (-5, 0, 5):
                        tot += 1
                        bt += frac(blue, bx + off * ca, by + off * sa)
                        rt += frac(road, bx + off * ca, by + off * sa)
                scores[key] = (round(bt / tot, 3), round(rt / tot, 3))
    return scores


def side_vertices(side):
    """The two grid vertices that bound a hex-side, rounded to whole pixels."""
    e1, e2 = shared_edge(*side)
    return (round(e1[0]), round(e1[1])), (round(e2[0]), round(e2[1]))


def merge_near(verts, tol):
    """Collapse vertex keys that are within `tol` px of each other."""
    keys = sorted(verts)
    groups = []
    for k in keys:
        for g in groups:
            if abs(k[0] - g[0][0]) <= tol and abs(k[1] - g[0][1]) <= tol:
                g.append(k)
                break
        else:
            groups.append([k])
    rep = {}
    for g in groups:
        r = (sum(v[0] for v in g) // len(g), sum(v[1] for v in g) // len(g))
        for v in g:
            rep[v] = r
    return rep


def local_components(blue, v, rad=18, dil=2):
    """Connected components of the blue mask in a small window around vertex v,
    after `dil` dilation steps (bridges the ~5 px white grid line)."""
    x, y = v
    y0, y1 = max(0, y - rad), min(blue.shape[0], y + rad + 1)
    x0, x1 = max(0, x - rad), min(blue.shape[1], x + rad + 1)
    sub = blue[y0:y1, x0:x1].copy()
    for _ in range(dil):
        nd = sub.copy()
        nd[1:, :] |= sub[:-1, :]
        nd[:-1, :] |= sub[1:, :]
        nd[:, 1:] |= sub[:, :-1]
        nd[:, :-1] |= sub[:, 1:]
        sub = nd
    lab = np.zeros(sub.shape, dtype=int)
    cur = 0
    for i in range(sub.shape[0]):
        for j in range(sub.shape[1]):
            if sub[i, j] and lab[i, j] == 0:
                cur += 1
                lab[i, j] = cur
                stack = [(i, j)]
                while stack:
                    a, b = stack.pop()
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        na, nb = a + da, b + db
                        if 0 <= na < sub.shape[0] and 0 <= nb < sub.shape[1] \
                                and sub[na, nb] and lab[na, nb] == 0:
                            lab[na, nb] = cur
                            stack.append((na, nb))
    return lab, y0, x0


def side_labels(blue, side, v, lab, y0, x0, reach=14):
    """Component labels of the blue pixels that belong to `side` and are within
    `reach` px of vertex `v`."""
    e1, e2 = shared_edge(*side)
    vx, vy = e2[0] - e1[0], e2[1] - e1[1]
    n = math.hypot(vx, vy) or 1.0
    ux, uy = vx / n, vy / n
    px, py = -uy, ux
    labels = set()
    for t in np.linspace(0.0, 1.0, 25):
        sx, sy = e1[0] + vx * t, e1[1] + vy * t
        if math.hypot(sx - v[0], sy - v[1]) > reach:
            continue
        for off in (-4, 0, 4):
            qx, qy = int(round(sx + off * px)), int(round(sy + off * py))
            if y0 <= qy < y0 + lab.shape[0] and x0 <= qx < x0 + lab.shape[1]:
                if blue[qy, qx] and lab[qy - y0, qx - x0]:
                    labels.add(lab[qy - y0, qx - x0])
    return labels


def build_chains(river, blue):
    """Group river sides into chains: two sides belong to the same chain when
    they share a grid vertex and the water is continuous through that vertex."""
    by_vertex = defaultdict(list)
    for s in river:
        for v in side_vertices(s):
            by_vertex[v].append(s)
    rep = merge_near(by_vertex, VERTEX_TOL)
    merged = defaultdict(list)
    for v, ss in by_vertex.items():
        merged[rep[v]].extend(ss)

    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    wet = {}
    for v, ss in merged.items():
        if len(ss) < 2:
            continue
        lab, y0, x0 = local_components(blue, v)
        per_side = {s: side_labels(blue, s, v, lab, y0, x0) for s in ss}
        wet[v] = disc_frac(blue, v[0], v[1], WET_RADIUS)
        for i, a in enumerate(ss):
            for b in ss[i + 1:]:
                if per_side[a] & per_side[b]:
                    union(a, b)

    groups = defaultdict(list)
    for s in river:
        groups[find(s)].append(s)
    return groups, wet



def chain_adjacency(chain, by_vertex, rep):
    """Vertex-sharing adjacency inside one chain."""
    adj = defaultdict(set)
    for v, ss in by_vertex.items():
        members = [s for s in ss if s in chain]
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                adj[a].add(b)
                adj[b].add(a)
    return adj


def order_chain(chain, by_vertex, rep):
    """Walk a chain into an ordered list of sides starting from an end."""
    adj = chain_adjacency(chain, by_vertex, rep)
    ends = [s for s in chain if len(adj[s]) <= 1]
    start = ends[0] if ends else chain[0]
    ordered = [start]
    seen = {start}
    cur = start
    while True:
        nxt = [n for n in adj[cur] if n not in seen]
        if not nxt:
            break
        cur = max(nxt, key=lambda n: len(adj[n]))
        seen.add(cur)
        ordered.append(cur)
    return ordered, adj, ends


def hid(pair):
    return '%02d%02d' % pair


def main():
    board = stitched()
    blue, road = masks(board)
    scores = scan_sides(blue, road)

    river = sorted(s for s, v in scores.items() if v[0] >= RIVER_FRAC)
    roads = sorted(s for s, v in scores.items() if v[1] >= ROAD_FRAC)

    by_vertex = defaultdict(list)
    for s in river:
        for v in side_vertices(s):
            by_vertex[v].append(s)
    rep = merge_near(by_vertex, VERTEX_TOL)
    groups, wet = build_chains(river, blue)

    chains = []
    for g in groups.values():
        ordered, adj, ends = order_chain(g, by_vertex, rep)
        chains.append((ordered, adj, ends))
    chains.sort(key=lambda c: len(c[0]), reverse=True)

    print('hex-sides scanned:', len(scores))
    print('river sides:', len(river), ' road sides:', len(roads))
    hist = defaultdict(int)
    for s, v in scores.items():
        if v[0] >= 0.15:
            hist[round(v[0], 1)] += 1
    print('blue-fraction histogram (>=0.15):', dict(sorted(hist.items())))
    print('river chains:', len(chains))
    for ordered, adj, ends in chains:
        print('  chain %2d  ends=%s' % (len(ordered),
                                        ' | '.join('%s-%s' % (hid(a), hid(b)) for a, b in ends)))
        print('    ' + ' '.join('%s-%s' % (hid(a), hid(b)) for a, b in ordered))

    out = {'river_sides': [[hid(a), hid(b)] for a, b in river],
           'road_sides': [[hid(a), hid(b)] for a, b in roads],
           'chains': [[list(s) for s in ordered] for ordered, _, _ in chains]}
    with open('_refs/sides_traced.json', 'w') as f:
        json.dump(out, f, indent=1)

    d = ImageDraw.Draw(board)
    for a, b in roads:
        e1, e2 = shared_edge(a, b)
        d.line([e1, e2], fill=(255, 0, 0), width=6)
    for a, b in river:
        e1, e2 = shared_edge(a, b)
        d.line([e1, e2], fill=(0, 0, 255), width=8)
    board.thumbnail((1400, 1400))
    board.save('_refs/sides_traced_overlay.png')
    print('wrote _refs/sides_traced_overlay.png')


if __name__ == '__main__':
    main()
