import json

m = json.load(open('data/game_model.json', encoding='utf-8'))
rules = m['rules']
for k in ['r204', 'r205', 'r206', 'r208', 'r209', 'r210', 'r211', 'r212',
          'r213', 'r214', 'r215', 'r216', 'r217', 'r218', 'r219', 'r222',
          'r226', 'r227', 'r228']:
    r = rules.get(k)
    print('=' * 20, k)
    print((r if isinstance(r, str) else str(r))[:2600])
