import numpy as np, sys, math, itertools
sys.path.insert(0, 'src')
import river_trace as rt
from PIL import Image

board = rt.stitched()
arr = np.array(board.convert('RGB')).astype(np.int32)
rr, gg, bb = arr[:,:,0], arr[:,:,1], arr[:,:,2]
blue = (bb > rr + 20) & (bb > 100) & (bb > gg + 5)
H, W = blue.shape

ys, xs = np.nonzero(blue)
pts = np.stack([xs, ys], axis=1).astype(np.float32)

def blue_near(p, rad):
    d = np.linalg.norm(pts - np.array(p, dtype=np.float32), axis=1)
    return pts[d <= rad]

sides = []
for a in range(1, 21):
    for b in range(1, 24):
        for nb in rt.neighbours(a, b):
            if (a, b) < nb:
                e1, e2 = rt.shared_edge((a, b), nb)
                seg = [(e1[0] + (e2[0]-e1[0])*t/20.0, e1[1] + (e2[1]-e1[1])*t/20.0) for t in range(21)]
                bf = sum(1 for p in seg if blue[int(round(p[1])), int(round(p[0]))]) / 21.0
                if bf >= 0.3:
                    sides.append(((a, b), nb, bf, e1, e2))

print('river sides:', len(sides))

vert = {}
for A, B, bf, e1, e2 in sides:
    for v in (e1, e2):
        vert.setdefault(v, []).append((A, B, bf))

out = []
for v, lst in sorted(vert.items(), key=lambda kv: -len(kv[1])):
    if len(lst) < 2:
        continue
    bp = blue_near(v, 25)
    if len(bp) == 0:
        gap = 99
    else:
        gap = float(np.linalg.norm(bp - np.array(v, dtype=np.float32), axis=1).min())
    for r in (6, 10, 14, 20):
        d = np.linalg.norm(bp - np.array(v, dtype=np.float32), axis=1) if len(bp) else np.array([])
        pass
    out.append((v, len(lst), gap, sorted(round(x[2], 3) for x in lst)))

out.sort(key=lambda t: t[2])
for v, n, gap, bfs in out:
    print('%s %d sides gap=%.1f bf=%s' % (v, n, gap, bfs))
