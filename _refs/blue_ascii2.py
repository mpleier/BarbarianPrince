import numpy as np, sys
sys.path.insert(0, 'src')
import river_trace as rt
from PIL import Image

board = rt.stitched()
W, H = board.size
arr = np.array(board.convert('RGB')).astype(np.int32)
rr, gg, bb = arr[:,:,0], arr[:,:,1], arr[:,:,2]
blue = (bb > rr + 20) & (bb > 100) & (bb > gg + 5)

CW, CH = 240, 120
lines = []
for y in range(CH):
    row = []
    for x in range(CW):
        block = blue[y*H//CH:(y+1)*H//CH, x*W//CW:(x+1)*W//CW]
        f = block.mean()
        row.append('#' if f > 0.35 else ('+' if f > 0.15 else ('.' if f > 0.05 else ' ')))
    lines.append(''.join(row))
open('_refs/blue_ascii2.txt', 'w').write('\n'.join(lines))
print('\n'.join(lines))
