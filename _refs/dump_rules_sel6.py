import json

m = json.load(open('data/game_model.json', encoding='utf-8'))
for k in ['r201', 'r202', 'r203', 'r229', 'r230']:
    r = m['rules'].get(k)
    print('=' * 18, k)
    print((r if isinstance(r, str) else str(r)).replace('\n', ' ')[:1800])
