import json, math, sys
sys.path.insert(0, 'src')
import river_trace as rt

data = json.load(open('_refs/sides_traced.json', encoding='utf-8'))
river = [tuple(map(tuple, s)) for s in data['river_sides']]
chains = [[tuple(map(tuple, s)) for s in ch] for ch in data['chains']]

board = rt.stitched()
W, H = board.size
CW, CH = 150, 84
grid = [[' '] * CW for _ in range(CH)]

def put(x, y, ch):
    cx = int(x * (CW - 1) / W)
    cy = int(y * (CH - 1) / H)
    if 0 <= cx < CW and 0 <= cy < CH:
        grid[cy][cx] = ch

for ci, ch in enumerate(chains):
    mark = '0123456789abcdefghij'[ci % 20]
    for a, b in ch:
        e1, e2 = rt.shared_edge(a, b)
        n = int(math.hypot(e2[0]-e1[0], e2[1]-e1[1])) + 1
        for t in range(n + 1):
            put(e1[0] + (e2[0]-e1[0]) * t / n, e1[1] + (e2[1]-e1[1]) * t / n, mark)

for row in grid:
    print(''.join(row))
with open('_refs/chain_ascii.txt', 'w', encoding='utf-8') as f:
    for row in grid:
        f.write(''.join(row) + '\n')
print()
for ci, ch in enumerate(chains):
    print(ci, len(ch), ' '.join('%s-%s' % (rt.hid(a), rt.hid(b)) for a, b in ch))
