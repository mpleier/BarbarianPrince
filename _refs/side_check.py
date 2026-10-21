import sys, json, math
sys.path.insert(0, r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\src')
from geometry import board_xy, parse_hex, neighbours, R

f = json.load(open(r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\data\features.json', encoding='utf-8'))
sides = [tuple(s) for s in f['river_sides']]
bad = []
for a, b in sides:
    if b not in neighbours(*parse_hex(a)):
        bad.append((a, b))
print('non-adjacent river pairs:', len(bad), 'of', len(sides))
print(bad[:40])

road = [tuple(s) for s in f['road_sides']]
badr = [(a, b) for a, b in road if b not in neighbours(*parse_hex(a))]
print('road sides:', len(road), 'non-adjacent:', len(badr))
print(badr[:20])
