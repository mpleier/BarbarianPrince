import json
h = json.load(open('_refs/hexes.json', encoding='utf-8'))
m = {x['id']: x['terrain'] for x in h}
terr = sorted(set(m.values()))
print(terr)
C = {t: chr(ord('a') + i) for i, t in enumerate(terr)}
for r in range(1, 24):
    print('row %2d ' % r + ''.join(C[m['%02d%02d' % (c, r)]] for c in range(1, 21)))
