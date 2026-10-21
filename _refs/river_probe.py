import sys, json, math
sys.path.insert(0, r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\src')
from geometry import board_xy, parse_hex, R

f = json.load(open(r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\data\features.json', encoding='utf-8'))
sides = [tuple(s) for s in f['river_sides']]


def shared_edge(a, b):
    ax, ay = board_xy(*parse_hex(a))
    bx, by = board_xy(*parse_hex(b))
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    px, py = -dy / d, dx / d
    return ((mx + px * R / 2, my + py * R / 2), (mx - px * R / 2, my - py * R / 2))


sel = ['0801-0902', '0802-0901', '0901-1002', '0902-1001', '1001-1102',
       '1002-1101', '1101-1202', '1202-1303', '1203-1302', '1302-1401',
       '0102-0201', '1301-1302', '1118-1119', '1017-1117']
for s in sel:
    a, b = s.split('-')
    for p in shared_edge(a, b):
        print(s, '->', round(p[0], 1), round(p[1], 1))
