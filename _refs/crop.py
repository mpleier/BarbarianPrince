"""Crop a zoomed region of the stitched overlay to inspect alignment."""
from PIL import Image

im = Image.open('_refs/board_stitch_small.jpg')
im.crop((0, 300, 700, 700)).resize((700, 400)).save('_refs/crop_left.jpg')
im.crop((300, 300, 1000, 700)).resize((700, 400)).save('_refs/crop_mid.jpg')
print(im.size)
