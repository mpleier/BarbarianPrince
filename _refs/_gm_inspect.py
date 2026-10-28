import json

gm = json.load(open('data/game_model.json', encoding='utf-8'))
print('top-level keys:', list(gm.keys()))
print()
print('meta:', json.dumps(gm.get('meta'), indent=1)[:600])
print()
print('geometry:', json.dumps(gm.get('geometry'), indent=1)[:400])
print()
grid = gm.get('grid', {})
print('grid entries:', len(grid))
first = list(grid.items())[0]
print('grid sample key:', first[0])
print('grid sample:', json.dumps(first[1], indent=1))
print()
rules = gm.get('rules', {})
print('rules count:', len(rules))
rk = list(rules.keys())[0]
print('rule sample', rk, ':', json.dumps(rules[rk], indent=1)[:200])
print()
idx = gm.get('index', {})
print('index keys:', list(idx.keys()))
for k in idx:
    v = idx[k]
    if isinstance(v, dict):
        print(f'  index.{k}: dict len={len(v)}')
        for kk in list(v)[:5]:
            print(f'      {kk}: {json.dumps(v[kk])[:80]}')
    elif isinstance(v, list):
        print(f'  index.{k}: list len={len(v)} sample={json.dumps(v[:8])}')
    else:
        print(f'  index.{k}: {v!r}')
print()
eo = gm.get('event_options', {})
print('event_options count:', len(eo))
ek = list(eo.keys())[0]
print('event_options sample', ek, ':', json.dumps(eo[ek], indent=1)[:400])
print()
tables = gm.get('tables', {})
print('model tables keys:', list(tables.keys()))
