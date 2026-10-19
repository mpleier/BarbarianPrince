import json
import sys

m = json.load(open('../data/game_model.json', encoding='utf-8'))
ids = sys.argv[1:] or ['r201', 'r202', 'r203', 'r204']
for rid in ids:
    sec = m['rules'][rid]
    print('=' * 70)
    print(rid, sec['title'])
    print(sec['text'])
