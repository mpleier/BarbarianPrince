from PIL import Image
import math

R = 106.0
DX, DY = 1.5 * R, math.sqrt(3) * R

def centre(col, row, x0, y0, r0):
    i = col - 1
    return x0 + DX * i, y0 + DY * (row - r0) + (i % 2) * DY / 2.0

im = Image.open('map1.jpg')
cx, cy = centre(12, 11, 377.0, 96.0, 1)
im.crop((int(cx - 420), int(cy - 420), int(cx + 420), int(cy + 420)).__str__() and (int(cx - 420), int(cy - 420), int(cx + 420), int(cy + 420))).save('crop_huldra3.png')