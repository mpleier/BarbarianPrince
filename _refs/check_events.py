import json
import re

e = json.load(open('../data/events.json', encoding='utf-8'))
want = [f'e{i:03d}' for i in range(1, 196)]
print('keys:', len(e))
print('missing:', [k for k in want if k not in e])

ls = open('events.txt', encoding='latin-1').read().splitlines()
print('lines:', len(ls))
titles = [(i, l.strip()) for i, l in enumerate(ls) if re.match(r'^e\d{3}\s', l.strip())]
print('title lines:', len(titles))
for i, t in titles[:10]:
    print(i, t)
