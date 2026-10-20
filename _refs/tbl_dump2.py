import json
import re

d = json.load(open('data/tables.json'))
print('=== RUINS_SEARCH ===')
for r in d['ruins_search']:
    print(r)

print('\n=== TREASURE_TABLE (all) ===')
for r in d['treasure_table']:
    print(r['code'], r['results'])
