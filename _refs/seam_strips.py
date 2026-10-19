"""Stack the bottom strip of map1 above the top strip of map2 to inspect the seam."""
from PIL import Image

m1 = Image.open('_refs/map1.jpg').convert('RGB')
m2 = Image.open('_refs/map2.jpg').convert('RGB')

# column-1 band: x = 250..1100
x0, x1 = 250, 1100
s1 = m1.crop((x0, 1950, x1, 2136))
s2 = m2.crop((x0, 0, x1, 260))
w = max(s1.width, s2.width)
h = s1.height + s2.height
out = Image.new('RGB', (w, h), (0, 0, 0))
out.paste(s1, (0, 0))
out.paste(s2, (0, s1.height))
out.save('_refs/seam_strips.png')
print('map1 strip y=1950..2136, map2 strip y=0..260 -> _refs/seam_strips.png')
