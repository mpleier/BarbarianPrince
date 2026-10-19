"""Find clean flat grid edges (length ~ R) and cluster their x-centres."""
import numpy as np
from PIL import Image

for name in ('map1.jpg', 'map2.jpg'):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    centres = []
    for y in range(A.shape[0]):
        row = white[y]
        x = 0
        W = len(row)
        while x < W:
            if row[x]:
                s = x
                while x < W and row[x]:
                    x += 1
                e = x - 1
                if 96 <= e - s + 1 <= 116:
                    centres.append((s + e) / 2.0)
            else:
                x += 1
    centres.sort()
    print(name, 'clean edges found:', len(centres))
    # cluster centres that are within 3 px of each other
    groups = []
    for c in centres:
        if groups and c - groups[-1][-1] <= 3:
            groups[-1].append(c)
        else:
            groups.append([c])
    means = [round(np.mean(g), 1) for g in groups if len(g) >= 3]
    print('   x-centres (>=3 hits):', means)
    if len(means) > 1:
        d = [means[i + 1] - means[i] for i in range(len(means) - 1)]
        print('   spacings:', [round(x, 1) for x in d])
    print()
