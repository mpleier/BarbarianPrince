from PIL import Image

im = Image.open('../_refs/map.jpg')
w, h = im.size
print(w, h)
# middle band, two halves
im.crop((0, 900, w // 2, 1700)).save('../_refs/crop_mid_left.png')
im.crop((w // 2, 900, w, 1700)).save('../_refs/crop_mid_right.png')
im.crop((0, 1500, w // 2, 2400)).save('../_refs/crop_bot_left2.png')
im.crop((w // 2, 1500, w, 2400)).save('../_refs/crop_bot_right2.png')