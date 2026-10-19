"""Robust lattice fit: detect flat hex edges, cluster them into columns/rows,
then least-squares fit x0, DX, y0, DY for each scan."""
import numpy as np
from PIL import Image

for name in ('map1.jpg', 'map2.jpg'):
    A = np.asarray(Image.open('_refs/' + name).convert('RGB'), dtype=np.int16)
    white = (A.min(axis=2) > 200)
    H, W = A.shape[:2]
    pts = []
    for y in range(H):
        row = white[y]
        x = 0
        while x < W:
            if row[x]:
                s = x
                while x < W and row[x]:
                    x += 1
                ln = x - s
                if 85 <= ln <= 130:
                    pts.append((y, (s + x - 1) / 2.0))
            else:
                x += 1
    pts.sort()
    # cluster by x
    clusters = []
    for y, cx in pts:
        placed = False
        for cl in clusters:
            if abs(cx - cl['x'] / cl['n']) < 25:
                cl['x'] += cx
                cl['n'] += 1
                cl['ys'].append(y)
                placed = True
                break
        if not placed:
            clusters.append({'x': cx, 'n': 1, 'ys': [y]})
    cols = sorted((c['x'] / c['n'] for c in clusters if c['n'] >= 4))
    print(name, 'n_cols=', len(cols))
    print('  col centres:', [round(c, 1) for c in cols])
    if len(cols) >= 3:
        k = np.arange(len(cols))
        DX, x0 = np.polyfit(k, cols, 1)
        print('  fit DX=%.2f x0=%.2f' % (DX, x0))
    # rows: take the column with the most edges and fit its y spacing
    best = max(clusters, key=lambda c: c['n'])
    ys = sorted(best['ys'])
    groups = []
    for y in ys:
        if groups and y == groups[-1][-1] + 1:
            groups[-1].append(y)
        else:
            groups.append([y])
    centres = [sum(g) / len(g) for g in groups]
    print('  busiest column x=%.1f edge ys=%s' % (best['x'] / best['n'], [round(c, 1) for c in centres]))
    if len(centres) >= 3:
        kk = np.arange(len(centres))
        DY, y0 = np.polyfit(kk, centres, 1)
        print('  fit DY=%.2f first_edge_y=%.2f' % (DY, y0))
    print()
