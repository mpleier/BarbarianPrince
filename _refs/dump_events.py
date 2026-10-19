import json

e = json.load(open('../data/events.json', encoding='utf-8'))
for c in ['e009', 'e013', 'e016', 'e022', 'e028', 'e035', 'e128']:
    print('=' * 70)
    print(c, e[c]['title'])
    print(e[c]['text'])