import json, sys
r = json.load(open('data/rules.json', encoding='utf-8'))
for k in sys.argv[1:]:
    v = r.get(k)
    if v:
        print('===', k, v.get('title'))
        print(v.get('text'))
        print()
