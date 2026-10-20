import json

e = json.load(open('data/events.json'))
for c in ['e003', 'e009', 'e050', 'e100', 'e037', 'e038', 'e039', 'e044']:
    v = e.get(c)
    if v:
        print('---', c, v['title'])
        print(v['text'])
        print()
