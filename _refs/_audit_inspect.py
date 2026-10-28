import json

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

for p in ['data/rules.json', 'data/events.json', 'data/tables.json',
          'data/event_options.json', 'data/features.json']:
    d = load(p)
    print('=' * 70)
    print(p, '->', type(d).__name__)
    if isinstance(d, dict):
        for k, v in d.items():
            extra = f' len={len(v)}' if isinstance(v, (list, dict)) else ''
            print(f'   {k}: {type(v).__name__}{extra}')
    elif isinstance(d, list):
        print('   len', len(d), '| sample:', json.dumps(d[0])[:180])

# tables.json sub-structure
t = load('data/tables.json')
print('=' * 70)
print('tables.json details:')
for k, v in t.items():
    if isinstance(v, dict):
        print(f'  {k}: dict keys={list(v)[:6]}...')
    elif isinstance(v, list):
        print(f'  {k}: list[{len(v)}] sample={json.dumps(v[0])[:120]}')
    else:
        print(f'  {k}: {v!r}')
