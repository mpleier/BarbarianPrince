import json

t = json.load(open('data/tables.json'))
print('--- OFFERINGS (r212) ---')
for r in t['offerings']:
    print(r['roll'], r['text'][:120])
print('--- AUDIENCE ---')
for r in t['audience']:
    print(r['roll'], r['text'][:120])
print('--- NEWS ---')
for r in t['news']:
    print(r['roll'], r['text'][:120])
