import sys, json
m = json.load(open('data/game_model.json', encoding='utf-8'))
for c in ['e002','e003','e004','e005','e021','e081','e098','e099','e100']:
    print('===', c, m['events'][c]['title'])
    print(m['events'][c]['text'])
    print()
