import json
d = json.load(open('data/tables.json', encoding='utf-8'))
for row in d['offerings']:
    print(row)
