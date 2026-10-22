import json

d = json.load(open('data/game_model.json', encoding='utf-8'))
rules = d['rules']
print('=== r212 full text ===')
print(rules['r212']['text'])
print()
print('=== rules mentioning staff/throne/king/win ===')
for k, v in rules.items():
    t = (v.get('title', '') + ' ' + v.get('text', '')).lower()
    if any(w in t for w in ('staff of command', 'throne', 'win the game', 'victor', 'kingdom is yours')):
        print(k, v.get('title'))
print()
print('=== offerings table ===')
for row in d['tables']['offerings']:
    print(row)
print()
print('=== events mentioning staff ===')
for k, v in d['events'].items():
    t = str(v).lower()
    if 'staff of command' in t:
        print(k, str(v)[:200])
