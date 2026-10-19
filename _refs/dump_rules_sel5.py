import json

m = json.load(open('data/game_model.json', encoding='utf-8'))
for k in ['r215', 'r216', 'r206', 'r208']:
    r = m['rules'].get(k)
    print('=' * 18, k)
    print((r if isinstance(r, str) else str(r)).replace('\n', ' '))
print('=' * 18, 'offerings table')
print(json.dumps(m['tables']['offerings'], indent=1)[:2500])
print('=' * 18, 'audience keys')
print(list(m['tables']['audience'].keys()))
