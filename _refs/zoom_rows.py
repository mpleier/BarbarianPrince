"""Zoom crops of the real scans for terrain spot-checking."""
from PIL import Image

im = Image.open('_refs/map1.jpg').convert('RGB')
im.crop((300, 0, 1400, 600)).save('_refs/zoom_row1.png')
im.crop((1400, 0, 2500, 600)).save('_refs/zoom_row1b.png')
im2 = Image.open('_refs/map2.jpg').convert('RGB')
im2.crop((300, 0, 1400, 600)).save('_refs/zoom_row13.png')
