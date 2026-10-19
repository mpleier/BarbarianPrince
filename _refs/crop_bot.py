from PIL import Image

for name in ['map1.jpg', 'map2.jpg']:
    im = Image.open(name)
    w, h = im.size
    im.crop((0, 2 * h // 3, w // 2, h)).save('bot_%s' % name)
    im.crop((w // 2, 2 * h // 3, w, h)).save('botr_%s' % name)