import json

t = json.load(open('../data/tables.json', encoding='utf-8'))
print('combat_table:')
for r in t['combat_table']:
    print(' ', r)
print()
print('special_possession_lines:', json.dumps(t['special_possession_lines'], indent=1)[:800])
print()
print('ruins_search:', json.dumps(t['ruins_search'], indent=1)[:600])
print()
print('hiring:', json.dumps(t['hiring'], indent=1)[:900])
print()
print('offerings:', json.dumps(t['offerings'], indent=1)[:900])
