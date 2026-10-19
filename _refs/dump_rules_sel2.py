import json

m = json.load(open('data/game_model.json', encoding='utf-8'))
rules = m['rules']
for k in ['r204', 'r205', 'r209', 'r210', 'r211', 'r212', 'r215', 'r217',
          'r222', 'r226', 'r227', 'r228']:
    r = rules.get(k)
    print('=' * 18, k)
    print((r if isinstance(r, str) else str(r)).replace('\n', ' ')[:1300])
