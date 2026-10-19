import re, zlib, sys

data = open(sys.argv[1], 'rb').read()
acc = []
for m in re.finditer(rb'stream\r?\n', data):
    start = m.end()
    end = data.find(b'endstream', start)
    if end < 0:
        continue
    raw = data[start:end]
    try:
        acc.append(zlib.decompress(raw).decode('latin-1'))
    except Exception:
        pass
s = '\n'.join(acc)
cells = []
for m in re.finditer(r'([0-9.]+) ([0-9.]+) ([0-9.]+) ([0-9.]+) re', s):
    x, y, w, h = map(float, m.groups())
    cells.append((y, x, w, h))
cells = sorted(set(cells))
for y, x, w, h in cells:
    print(f"y={y:8.2f} x={x:8.2f} w={w:7.2f} h={h:7.2f}")
