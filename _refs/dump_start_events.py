import json

e = json.load(open('../data/events.json', encoding='utf-8'))
for c in ['e001', 'e002', 'e050', 'e194', 'e195', 'e144', 'e146']:
    print('=' * 70)
    print(c, e[c]['title'])
    print(e[c]['text'])