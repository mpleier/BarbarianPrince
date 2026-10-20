import json

d = json.load(open('data/tables.json'))
for r in d['travel_table']:
    print(r)
