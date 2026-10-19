import json

m = json.load(open('data/game_model.json', encoding='utf-8'))
print(sorted(m['tables'].keys()))
for k in ['r212', 'r215', 'r217', 'r218', 'r219']:
    r = m['rules'].get(k)
    print('=' * 18, k)
    print((r if isinstance(r, str) else str(r)).replace('\n', ' ')[:2500])
