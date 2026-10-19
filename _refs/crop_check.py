import os

from PIL import Image

REFS = os.path.dirname(os.path.abspath(__file__))
im = Image.open(os.path.join(REFS, 'map1.jpg'))
im.crop((0, 0, 700, 500)).save(os.path.join(REFS, 'crop_top_left.png'))
im.crop((1700, 1000, 2400, 1700)).save(os.path.join(REFS, 'crop_huldra.png'))
im.crop((2400, 1400, 3100, 2100)).save(os.path.join(REFS, 'crop_drogat.png'))
print('done')

