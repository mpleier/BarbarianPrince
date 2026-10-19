"""Stitch map1.jpg + map2.jpg into one 20x23 board frame and draw the grid.

Usage: python _refs/stitch_board.py [out.png]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from PIL import Image, ImageDraw

from geometry import NC, NR, R, DX, DY, SCANS, BOARD_Y_OFF, board_xy, board_corners

SQ3 = math.sqrt(3.0)

def main(out='_refs/board_stitch.png'):
    im1 = Image.open('_refs/map1.jpg').convert('RGB')
    im2 = Image.open('_refs/map2.jpg').convert('RGB')
    W = max(im1.width, im2.width)
    off = {n: BOARD_Y_OFF[n] for n in SCANS}
    H = int(max(im1.height + off['map1.jpg'], im2.height + off['map2.jpg'])) + 20
    board = Image.new('RGB', (W, H), (255, 255, 255))
    for name, img in (('map1.jpg', im1), ('map2.jpg', im2)):
        board.paste(img, (0, int(round(off[name]))))

    d = ImageDraw.Draw(board)
    for c in range(1, NC + 1):
        for r in range(1, NR + 1):
            pts = board_corners(c, r)
            d.polygon(pts, outline=(255, 0, 0))
            cx, cy = board_xy(c, r)
            d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(0, 0, 255))
            d.text((cx - 12, cy - 8), '%02d%02d' % (c, r), fill=(255, 255, 0))

    small = board.copy()
    small.thumbnail((1100, 1100))
    small.save(out)
    print('wrote', out, board.size, '->', small.size)
    print('BOARD_Y_OFF =', off)

    # Full-resolution zoom on the stitch line so the seam can be inspected.
    from geometry import SEAM_Y
    y0 = int(SEAM_Y) - 260
    y1 = int(SEAM_Y) + 260
    board.crop((200, y0, 1100, y1)).save('_refs/seam_zoom.png')
    print('wrote _refs/seam_zoom.png  (seam at unified y = %.2f)' % SEAM_Y)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '_refs/board_stitch.png')
