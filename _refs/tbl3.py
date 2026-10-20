import json

d = json.load(open('data/tables.json'))
rs = d['ruins_search']
print(type(rs))
print(json.dumps(rs, indent=1)[:1500])
print('\nNEWS:')
for r in d['news']:
    print(r['roll'], '->', r['text'][:80])
