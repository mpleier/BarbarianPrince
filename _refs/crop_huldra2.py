from PIL import Image
import math

R = 106.0
DX, DY = 1.5 * R, math.sqrt(3) * R

def centre(col, row, x0, y0, r0):
    i = col - 1
    return x0 + DX * i, y0 + DY * (row - r0) + (i % 2) * DY / 2.0

im = Image.open('map1.jpg')
cx, cy = centre(12, 12, 377.0, 96.0, 1)
im.crop((int(cx - 320), int(cy - 320), int(cx + 320), int(cy + 320))).save('crop_huldra2.png')

im2 = Image.open('map2.jpg')
cx, cy = centre(19, 23, 377.0, 199.0, 13)
im2.crop((int(cx - 260), int(cy - 260), int(cx + 260), int(cy + 260))).save('crop_aeravir.png')