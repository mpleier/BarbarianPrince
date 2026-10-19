"""Find the single R that best fits BOTH scans, anchoring each scan on its own
first printed grid line so the seam stays continuous by construction."""
import math
import numpy as np

SQ3 = math.sqrt(3.0)

map1_lines = [190.0, 373.5, 557.5, 741.5, 924.0, 1107.0,
              1291.0, 1473.5, 1657.5, 1842.0, 2027.0]          # 1/2 .. 11/12
map2_lines = [111.5, 297.0, 482.5, 666.5, 850.5, 1034.5,
              1218.5, 1402.0, 1586.0, 1770.5, 1955.0]          # 12/13 .. 22/23

map1_cols = [(2, 537.9), (3, 697.3), (4, 856.3), (5, 1017.5), (7, 1328.4),
             (8, 1487.7), (9, 1648.6), (10, 1807.2), (11, 1966.6),
             (12, 2125.6), (13, 2284.6)]
map2_cols = [(c, v) for c, v in zip(range(2, 21),
             [543.0, 703.9, 863.0, 1022.5, 1175.9, 1333.5, 1493.2,
              1651.9, 1811.1, 1971.4, 2131.5, 2279.8, 2439.7,
              2598.5, 2757.6, 2917.6, 3077.1, 3236.8, 3395.0])]


def worst(R):
    DY = SQ3 * R
    DX = 1.5 * R
    y0_1 = map1_lines[0] - DY / 2
    r1 = [map1_lines[k] - (y0_1 + (k + 0.5) * DY) for k in range(len(map1_lines))]
    y0_2 = map2_lines[0] + DY / 2
    r2 = [map2_lines[j] - (y0_2 + (j - 0.5) * DY) for j in range(len(map2_lines))]
    x0a = map1_cols[0][1] - DX * (map1_cols[0][0] - 1)
    c1 = [v - (x0a + DX * (c - 1)) for c, v in map1_cols]
    x0b = map2_cols[0][1] - DX * (map2_cols[0][0] - 1)
    c2 = [v - (x0b + DX * (c - 1)) for c, v in map2_cols]
    allr = r1 + r2 + c1 + c2
    return (max(map(abs, r1)), max(map(abs, r2)),
            max(map(abs, c1)), max(map(abs, c2)), max(map(abs, allr)))


best = None
for R in np.arange(104.0, 108.0, 0.01):
    w = worst(float(R))
    if best is None or w[4] < best[1][4]:
        best = (float(R), w)
print('best R = %.2f  worst residual = %.2f px' % (best[0], best[1][4]))
for R in (105.8, 106.0, 106.1, 106.2, 106.3, 106.4):
    w = worst(R)
    print('R=%.2f -> rows m1 %.2f  rows m2 %.2f  cols m1 %.2f  cols m2 %.2f  worst %.2f'
          % (R, w[0], w[1], w[2], w[3], w[4]))
