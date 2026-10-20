import json

d = json.load(open('data/tables.json'))
print('=== HIRING ===')
for r in d['hiring']:
    print(r['roll'], '->', r['text'][:90])
print('\n=== AUDIENCE ===')
for r in d['audience']:
    print(r['roll'], '->', r['text'][:90])
print('\n=== SPECIAL_TRAVEL_REFERENCE ===')
for r in d['special_travel_reference'][:12]:
    print(r)
