import numpy as np, sys
sys.path.insert(0, 'src')
import river_trace as rt
from PIL import Image

board = rt.stitched()
arr = np.array(board.convert('RGB')).astype(np.int32)
rr, gg, bb = arr[:,:,0], arr[:,:,1], arr[:,:,2]
blue = (bb > rr + 20) & (bb > 100) & (bb > gg + 5)

def show(v, rad=22):
    x, y = v
    print('vertex', v)
    for yy in range(y-rad, y+rad+1, 2):
        line = ''
        for xx in range(x-rad, x+rad+1, 2):
            if 0 <= yy < blue.shape[0] and 0 <= xx < blue.shape[1]:
                line += '#' if blue[yy, xx] else ('o' if bb[yy, xx] > 120 else '.')
            else:
                line += ' '
        print(line)
    print()

for v in [(1755, 3036), (1702, 2944), (1649, 2852), (1490, 2760), (1437, 2668), (1384, 2576)]:
    show(v)
