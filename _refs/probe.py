import numpy as np
from build_map import sample_hex

def feats(px):
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    lum = px.mean(axis=1)
    return np.array([
        r.mean(), g.mean(), b.mean(),
        (lum < 90).mean(),
        (lum > 200).mean(),
        ((r > g + 12) & (r > b + 12)).mean(),
        ((g > r + 12) & (g > b + 12)).mean(),
        ((b > g + 8) & (b > r + 8)).mean(),
        ((r > 150) & (g > 150) & (b < 130)).mean(),
    ])

for h in ['0411','0511','0312','1212','1412','1812','1612','1912','0214','0313','0512','0412','0612','0113','1113','1213','1313','1413','1513','1613','1713','1813','1913','2013']:
    px = sample_hex(int(h[:2]), int(h[2:]))
    print(h, len(px), np.round(feats(px), 3))
