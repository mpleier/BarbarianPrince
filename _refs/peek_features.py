import json
import os

REFS = os.path.dirname(os.path.abspath(__file__))
for name in ['roadhexes.json', 'hexsides.json']:
    p = os.path.join(REFS, name)
    if not os.path.exists(p):
        print(name, 'missing')
        continue
    d = json.load(open(p, encoding='utf-8'))
    print('---', name, type(d), len(d))
    if isinstance(d, dict):
        items = list(d.items())[:15]
        print(items)
    else:
        print(d[:5])