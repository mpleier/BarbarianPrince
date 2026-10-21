import numpy as np, sys, math
from collections import defaultdict
sys.path.insert(0, '_refs')
sys.path.insert(0, 'src')
import river_trace as rt

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

def sh(s):
    return '%s-%s' % (rt.hid(s[0]), rt.hid(s[1]))

lines = []
for v, ss in sorted(merged.items(), key=lambda kv: -len(kv[1])):
    if len(ss) < 2:
        continue
    lab, y0, x0 = rt.local_components(blue, v)
    per = {s: rt.side_labels(blue, s, v, lab, y0, x0) for s in ss}
    conn = []
    for i, a in enumerate(ss):
        for b in ss[i+1:]:
            conn.append((a, b, bool(per[a] & per[b])))
    lines.append('vertex %s  disc=%.3f  sides=%s' % (v, rt.disc_frac(blue, v[0], v[1], rt.WET_RADIUS),
                     ' '.join(sh(s) for s in ss)))
    for a, b, c in conn:
        lines.append('   %s  %s  -> %s   labels %s vs %s' % (sh(a), sh(b),
                     'CONNECTED' if c else 'no', sorted(per[a]), sorted(per[b])))

open('_refs/vertex_report.txt', 'w').write('\n'.join(lines))
print('vertices with >=2 river sides:', sum(1 for v, ss in merged.items() if len(ss) >= 2))
print('lines written:', len(lines))
