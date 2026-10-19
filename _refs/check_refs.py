import json
import re

r = json.load(open('../data/rules.json', encoding='utf-8'))
ids = sorted(int(k[1:]) for k in r)
print('rule ids:', ids)
print('gaps:', [i for i in range(ids[0], ids[-1] + 1) if i not in set(ids)])

e = json.load(open('../data/events.json', encoding='utf-8'))
hits = [k for k, v in e.items() if re.search(r'\b\d{4}\b', v['text'])]
print('events naming a 4-digit number:', len(hits))
print(hits[:20])
for k in hits[:5]:
    print(k, re.findall(r'\b\d{4}\b', e[k]['text']))
