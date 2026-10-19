from PIL import Image

for name in ['map1.jpg', 'map2.jpg']:
    im = Image.open(name)
    w, h = im.size
    print(name, w, h)
    im.crop((0, h // 3, w // 2, 2 * h // 3)).save('mid_%s' % name)
    im.crop((w // 2, h // 3, w, 2 * h // 3)).save('midr_%s' % name)