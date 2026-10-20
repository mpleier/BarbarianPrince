import json, re

e = json.load(open('data/events.json'))
n = 0
for c, v in e.items():
    t = v['text']
    idx = t.find('Your options are:')
    if idx < 0:
        continue
    body = t[idx + len('Your options are:'):]
    stars = [m.start() for m in re.finditer(r'\*', body)]
    if len(stars) > 1:
        n += 1
        print(c, [body[s:s+25] for s in stars])
print('events with >1 star:', n)
