import json

r = json.load(open('../data/rules.json', encoding='utf-8'))
print(r['r220']['title'])
print(r['r220']['text'])
