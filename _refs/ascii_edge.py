import numpy as np
from PIL import Image

im = Image.open('_refs/map1.jpg').convert('RGB')
im.crop((250, 0, 700, 420)).resize((900, 840)).save('_refs/hex0101_zoom.png')
print('wrote _refs/hex0101_zoom.png (x 250-700, y 0-420, 2x zoom)')





