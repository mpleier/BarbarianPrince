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
        txt = zlib.decompress(raw)
    except Exception:
        continue
    acc.append(txt.decode('latin-1'))
open(sys.argv[2], 'w', encoding='utf-8').write('\n===PAGE===\n'.join(acc))
print(len(acc))
