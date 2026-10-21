import json, math, os, sys
from collections import defaultdict
sys.path.insert(0, 'src')
import river_trace as rt
from geometry import board_xy

board = rt.stitched()
blue, road = rt.masks(board)
scores = rt.scan_sides(blue, road)
river = sorted(s for s, v in scores.items() if v[0] >= rt.RIVER_FRAC)

by_vertex = defaultdict(list)
for s in river:
    for v in rt.side_vertices(s):
        by_vertex[v].append(s)
rep = rt.merge_near(by_vertex, rt.VERTEX_TOL)
merged = defaultdict(list)
for v, ss in by_vertex.items():
    merged[rep[v]].extend(ss)

rows = []
for v, ss in merged.items():
    if len(ss) < 2:
        continue
    f = rt.disc_frac(blue, v[0], v[1], rt.WET_RADIUS)
    rows.append((f, v, sorted(set(ss))))
rows.sort()
for f, v, ss in rows:
    print('%.3f' % f, v, ['%s-%s' % (rt.hid(a), rt.hid(b)) for a, b in ss])
print('total junction vertices:', len(rows))
