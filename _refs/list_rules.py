import json

m = json.load(open('../data/game_model.json', encoding='utf-8'))
for rid, sec in m['rules'].items():
    print(rid, '|', sec['title'], '| len', len(sec['text']))
