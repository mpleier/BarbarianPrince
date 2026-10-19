import re, zlib, sys

path = sys.argv[1]
data = open(path, 'rb').read()
out = []
for m in re.finditer(rb'stream\r?\n', data):
    start = m.end()
    end = data.find(b'endstream', start)
    if end < 0:
        continue
    raw = data[start:end]
    try:
        txt = zlib.decompress(raw)
    except Exception:
        try:
            txt = zlib.decompressobj(-15).decompress(raw)
        except Exception:
            continue
    s = txt.decode('latin-1')
    # find text with positions
    cur = None
    for mm in re.finditer(r'([0-9.]+) ([0-9.]+) Td|([0-9.]+) ([0-9.]+) Tz|\((?:[^()\\]|\\.)*\)\s*(Tj|TJ)|\[(?:[^\]]|\\.)*\]\s*TJ', s):
        tok = mm.group(0)
        if tok.endswith('Td') or tok.endswith('Tz'):
            cur = (float(mm.group(1)), float(mm.group(2)))
        else:
            out.append((cur, tok))
    out.append((None, '\n---PAGE---'))

with open(sys.argv[2], 'w', encoding='utf-8') as f:
    for pos, tok in out:
        f.write(f"{pos}\t{tok}\n")
print(len(out))
