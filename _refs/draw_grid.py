from PIL import Image, ImageDraw

R = 106.0
SQ3 = 1.7320508
DX, DY = 1.5 * R, SQ3 * R
x0, y0 = 377.0, 96.0

A = Image.open('map1.jpg').convert('RGB')
D = ImageDraw.Draw(A)
for col in range(1, 7):
    for row in range(1, 8):
        cx = x0 + DX * (col - 1)
        cy = y0 + DY * (row - 1) + ((col - 1) % 2) * DY / 2
        D.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(255, 0, 0))
        D.text((cx + 7, cy - 8), f'{col:02d}{row:02d}', fill=(255, 0, 0))
A.crop((200, 0, 1300, 900)).save('gridcheck2.png')
print('ok')
