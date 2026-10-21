import numpy as np, sys
sys.path.insert(0, '_refs'); sys.path.insert(0, 'src')
import river_trace as rt
from PIL import Image

board = rt.stitched()
blue, road = rt.masks(board)

def mask_crop(box, scale=2):
    x0, y0, x1, y1 = box
    sub = blue[y0:y1, x0:x1]
    img = Image.fromarray((sub.astype(np.uint8) * 255))
    img = img.resize(((x1-x0)*scale, (y1-y0)*scale), Image.NEAREST)
    return img

mask_crop((1620, 2900, 1960, 3160), 2).save('_refs/mask_v1.png')
mask_crop((1780, 3880, 2000, 4060), 3).save('_refs/mask_v2.png')
mask_crop((2150, 3600, 2350, 3760), 3).save('_refs/mask_v3.png')
mask_crop((3050, 1650, 3250, 1850), 3).save('_refs/mask_v4.png')
print('ok')
