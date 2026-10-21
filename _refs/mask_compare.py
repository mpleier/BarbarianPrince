import numpy as np, sys, math
from collections import defaultdict
sys.path.insert(0, '_refs'); sys.path.insert(0, 'src')
import river_trace as rt
from PIL import Image

board = rt.stitched()
a = np.array(board).astype(np.int32)
rr, gg, bb = a[:,:,0], a[:,:,1], a[:,:,2]
hsv = np.array(board.convert('HSV')).astype(np.int32)
H, S, V = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]

old_blue = (bb > rr + 20) & (bb > 100) & (bb > gg + 5)
new_blue = (H >= 125) & (H <= 165) & (S >= 60) & (V >= 90)

def scan(mask):
    out = {}
    for c in range(1, 21):
        for r in range(1, 24):
            for hid in rt.neighbours(c, r).values():
                nc, nr = int(hid[:2]), int(hid[2:])
                key = tuple(sorted(((c, r), (nc, nr))))
                if key in out:
                    continue
                e1, e2 = rt.shared_edge((c, r), (nc, nr))
                ang = math.atan2(e2[1]-e1[1], e2[0]-e1[0]) + math.pi/2
                ca, sa = math.cos(ang), math.sin(ang)
                hits = tot = 0
                for t in np.linspace(0.05, 0.95, 40):
                    x, y = e1[0] + (e2[0]-e1[0])*t, e1[1] + (e2[1]-e1[1])*t
                    for off in (-5, 0, 5):
                        tot += 1
                        hits += rt.frac(mask, x + off*ca, y + off*sa)
                out[key] = hits / tot
    return out

so = scan(old_blue)
sn = scan(new_blue)
old_set = {s for s, v in so.items() if v >= 0.5}
new_set = {s for s, v in sn.items() if v >= 0.5}
lines = []
lines.append('old blue mask: %d sides >=0.5' % len(old_set))
lines.append('new blue mask: %d sides >=0.5' % len(new_set))
lines.append('only old: %s' % sorted(rt.hid(a)+rt.hid(b) for a,b in old_set-new_set))
lines.append('only new: %s' % sorted(rt.hid(a)+rt.hid(b) for a,b in new_set-old_set))
hist = defaultdict(int)
for s, v in sn.items():
    if v >= 0.15:
        hist[round(v,1)] += 1
lines.append('new histogram: %s' % dict(sorted(hist.items())))
open('_refs/mask_compare.txt','w').write('\n'.join(lines))
print('\n'.join(lines[:5]))
