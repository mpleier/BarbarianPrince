import json, re, collections

s = open('_refs/hexfeat.txt', 'rb').read().decode('latin-1')
lines = [l for l in s.splitlines() if l.strip()]
print('hexfeat lines:', len(lines))
ids = []
for l in lines:
    m = re.match(r'\s*(\d{4})\s', l)
    if m:
        ids.append(m.group(1))
print('ids:', len(ids))
rows = collections.Counter(i[:2] for i in ids)
cols = collections.Counter(i[2:] for i in ids)
print('by first two digits:', sorted(rows.items()))
print('by last two digits:', sorted(cols.items()))

full = {'%02d%02d' % (c, r) for c in range(1, 21) for r in range(1, 24)}
missing = sorted(full - set(ids))
print('missing from hexfeat:', len(missing), missing)

hs = json.load(open('_refs/hexsides.json'))
print('sides:', len(hs))
riv = [k for k, v in hs.items() if v[0] > 0.35]
road = [k for k, v in hs.items() if v[1] > 0.3]
print('river sides:', len(riv))
print('road sides:', len(road))
print(riv[:40])
print(road[:40])
