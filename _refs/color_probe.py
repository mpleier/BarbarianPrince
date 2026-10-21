import numpy as np, sys, math
from collections import defaultdict
sys.path.insert(0, '_refs'); sys.path.insert(0, 'src')
import river_trace as rt
from PIL import Image

board = rt.stitched()
blue, road = rt.masks(board)
scores = rt.scan_sides(blue, road)
river = sorted(s for s, v in scores.items() if v[0] >= rt.RIVER_FRAC)
nonriver = sorted(s for s, v in scores.items() if v[0] < 0.2)

arr = np.array(board).astype(np.float32) / 255.0
hsv = np.array(Image.open('_refs/board_full.png').convert('HSV')).astype(np.int32)

def sample(side, n=9):
    e1, e2 = rt.shared_edge(*side)
    out = []
    for t in np.linspace(0.2, 0.8, n):
        x, y = int(round(e1[0] + (e2[0]-e1[0])*t)), int(round(e1[1] + (e2[1]-e1[1])*t))
        out.append((tuple(arr[y, x]), tuple(hsv[y, x])))
    return out

print('=== RIVER side samples (RGB, HSV) ===')
for s in river[:12]:
    for rgb, hv in sample(s, 3):
        print('%s-%s  rgb=%s hsv=%s' % (rt.hid(s[0]), rt.hid(s[1]),
              tuple(int(v*255) for v in rgb), tuple(int(v) for v in hv)))
print()
print('=== NON-river side samples ===')
for s in nonriver[:12]:
    for rgb, hv in sample(s, 3):
        print('%s-%s  rgb=%s hsv=%s' % (rt.hid(s[0]), rt.hid(s[1]),
              tuple(int(v*255) for v in rgb), tuple(int(v) for v in hv)))
