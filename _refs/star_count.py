import sys, json
m = json.load(open('data/game_model.json', encoding='utf-8'))
multi = 0
for c, ev in m['events'].items():
    t = ev['text']
    if 'Your options are:' not in t:
        continue
    body = t[t.find('Your options are:') + len('Your options are:'):]
    n = body.count('*')
    if n > 1:
        multi += 1
        print(c, 'stars:', n)
        print('   ', body[:200])
print('events with >1 star:', multi)
