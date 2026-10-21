import os, sys
sys.path.insert(0, 'src')
import numpy as np
import river_trace as rt

board = rt.stitched()
blue, road = rt.masks(board)
H, W = blue.shape
cols, rows = 120, 80
out = []
for r in range(rows):
    line = []
    for c in range(cols):
        y0, y1 = int(r * H / rows), int((r + 1) * H / rows)
        x0, x1 = int(c * W / cols), int((c + 1) * W / cols)
        b = blue[y0:y1, x0:x1].mean()
        o = road[y0:y1, x0:x1].mean()
        if b > 0.25:
            line.append('#')
        elif b > 0.08:
            line.append('.')
        elif o > 0.25:
            line.append('=')
        elif o > 0.08:
            line.append('-')
        else:
            line.append(' ')
    out.append(''.join(line))
print('\n'.join(out))
