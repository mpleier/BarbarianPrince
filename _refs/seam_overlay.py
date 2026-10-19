"""Crop the seam region and overlay the model hex outlines so the alignment
can be inspected visually at full resolution."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from PIL import Image, ImageDraw

from geometry import NC, R, DX, DY, SCANS, BOARD_Y_OFF, SEAM_Y, board_xy, board_corners

im1 = Image.open('_refs/map1.jpg').convert('RGB')
im2 = Image.open('_refs/map2.jpg').convert('RGB')
W = max(im1.width, im2.width)
H = int(max(im1.height, im2.height + BOARD_Y_OFF['map2.jpg'])) + 20
board = Image.new('RGB', (W, H), (255, 255, 255))
board.paste(im1, (0, 0))
board.paste(im2, (0, int(round(BOARD_Y_OFF['map2.jpg']))))

d = ImageDraw.Draw(board)
for c in range(1, NC + 1):
    for r in (12, 13):
        pts = board_corners(c, r)
        d.line(pts + pts[0:1], fill=(255, 0, 0), width=2)

y0, y1 = int(SEAM_Y) - 300, int(SEAM_Y) + 300
crop = board.crop((250, y0, 1250, y1))
crop.save('_refs/seam_overlay.png')
print('wrote _refs/seam_overlay.png  seam y = %.2f' % SEAM_Y)
