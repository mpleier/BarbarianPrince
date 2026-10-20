import sys, json
sys.path.insert(0, 'src')
from game_model import GameModel

m = GameModel(json.load(open('data/game_model.json', encoding='utf-8')))
print('=== OFFERINGS (r212) ===')
for r in m.tables['offerings']:
    print(r)
print()
print('=== NEWS (r209) ===')
for r in m.tables['news']:
    print(r['roll'], '|', r['text'])
