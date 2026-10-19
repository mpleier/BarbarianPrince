"""Overlay the modelled grid on a scan region and save a crop for inspection."""
import math
import sys

from PIL import Image, ImageDraw

SQ3 = math.sqrt(3.0)
R = 106.0
DX = 1.5 * R
DY = SQ3 * R


def draw(x0, y0, first_row, region, out, scan):
    im = Image.open('_refs/' + scan).convert('RGB')
    d = ImageDraw.Draw(im)
    for c in range(1, 21):
        for r in range(first_row, first_row + 23):
            cx = x0 + DX * (c - 1)
            cy = y0 + DY * (r - first_row) + (c - 1) % 2 * DY / 2.0
            if not (region[0] - R <= cx <= region[2] + R and
                    region[1] - R <= cy <= region[3] + R):
                continue
            pts = [(cx + R * math.cos(math.radians(a)),
                    cy + R * math.sin(math.radians(a))) for a in range(0, 360, 60)]
            d.polygon(pts, outline=(255, 0, 0))
            d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(0, 0, 255))
    im.crop(region).save(out)
    print('wrote', out)


if __name__ == '__main__':
    # right-hand columns of map1 (col 18-20, rows 1-4)
    draw(377.0, 98.2, 1, (2900, 60, 3510, 700), '_refs/overlay_right_map1.png', 'map1.jpg')
    # left-hand columns of map2 (col 1-4, rows 13-17)
    draw(377.0, 203.3, 13, (200, 60, 900, 700), '_refs/overlay_left_map2.png', 'map2.jpg')
    # bottom rows of map2
    draw(377.0, 203.3, 13, (300, 1800, 1100, 2148), '_refs/overlay_bottom_map2.png', 'map2.jpg')
