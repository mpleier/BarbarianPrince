import re, zlib, sys

data = open(sys.argv[1], 'rb').read()
items = []
for m in re.finditer(rb'stream\r?\n', data):
    start = m.end()
    end = data.find(b'endstream', start)
    if end < 0:
        continue
    raw = data[start:end]
    try:
        s = zlib.decompress(raw).decode('latin-1')
    except Exception:
        continue
    x = y = 0.0
    for tok in re.findall(
        r'(?:[0-9.]+) (?:[0-9.]+) (?:[0-9.]+) (?:[0-9.]+) (?:[0-9.]+) (?:[0-9.]+) T[mM]'
        r'|(?:[0-9.]+) (?:[0-9.]+) T[dD]'
        r'|\((?:[^()\\]|\\.)*\)'
        r'|\[(?:[^\]]|\\.)*\]TJ', s):
        if tok.endswith('Tm') or tok.endswith('TM'):
            nums = [float(v) for v in tok.split()[:6]]
            x, y = nums[4], nums[5]
        elif tok.endswith('Td') or tok.endswith('TD'):
            nums = [float(v) for v in tok.split()[:2]]
            x += nums[0]
            y += nums[1]
        else:
            items.append((y, x, tok))
items.sort(key=lambda t: (-t[0], t[1]))
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    for y, x, t in items:
        f.write(f"{y:8.2f} {x:8.2f} {t}\n")
print(len(items))
