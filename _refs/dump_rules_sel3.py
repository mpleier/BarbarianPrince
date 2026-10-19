import json

m = json.load(open('data/game_model.json', encoding='utf-8'))
rules = m['rules']
for k in ['r210', 'r211', 'r212', 'r213', 'r214', 'r215', 'r217', 'r218', 'r219']:
    r = rules.get(k)
    print('=' * 18, k)
    print((r if isinstance(r, str) else str(r)).replace('\n', ' ')[:2200])
print('=' * 18, 'news table')
print(json.dumps(m['tables'].get('news'), indent=1)[:3000])
print('=' * 18, 'hiring table')
print(json.dumps(m['tables'].get('hiring'), indent=1)[:2000])
