"""Crop a region of map1.jpg for visual terrain verification."""
from PIL import Image
from geometry import NC, NR, R, DX, DY, SCANS, board_xy

im = Image.open('_refs/map1.jpg').convert('RGB')
W, H = im.size

# rows 1-6, cols 1-10
xs = [board_xy(c, r)[0] for c in range(1, 11) for r in range(1, 7)]
ys = [board_xy(c, r)[1] for c in range(1, 11) for r in range(1, 7)]
x0, x1 = max(0, min(xs) - R), min(W, max(xs) + R)
y0, y1 = max(0, min(ys) - R), min(H, max(ys) + R)
im.crop((int(x0), int(y0), int(x1), int(y1))).save('_refs/verify_tl.png')
print('saved', x0, y0, x1, y1)
