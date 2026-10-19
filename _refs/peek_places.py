import json
import re

m = json.load(open('../data/game_model.json', encoding='utf-8'))
print('hex_events:', m['index']['hex_events'])

names = set()
for rid, sec in m['rules'].items():
    for mm in re.finditer(r'([A-Z][A-Za-z\'\-\s]{0,20}(Castle|Temple|Town|Village|Ruins|Keep|Fort|Abbey|Monastery))', sec['text']):
        names.add(mm.group(1).strip())
print('place-like names in rules:')
for n in sorted(names):
    print(' ', n)