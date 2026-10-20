import json

e = json.load(open('data/events.json'))
codes = ['e131', 'e132', 'e133', 'e134', 'e135', 'e136', 'e137', 'e138',
         'e139', 'e035']
for c in codes:
    v = e.get(c)
    if v:
        print(c, v['title'], '|', v['text'][:200])
        print()
