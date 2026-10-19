import re

t = open('_refs/rules_raw.txt', 'rb').read().decode('latin-1')
clean = re.sub(r'[^\x09\x0a\x20-\x7e]', ' ', t)
for kw in ['Combat Table', 'Treasure Table', 'Hiring', 'Audience', 'Offerings', 'News', 'r226', 'r210', 'r211', 'r212', 'r219', 'r220c']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), clean)]
    print('===', kw, len(idxs), idxs[:10])
    for i in idxs[:2]:
        print(repr(clean[max(0, i-300):i+900]))
        print('---')
