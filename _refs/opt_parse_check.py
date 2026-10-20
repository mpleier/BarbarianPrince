import sys, json
sys.path.insert(0, 'src')
from engine import parse_options
from game_model import GameModel

model = GameModel(json.load(open('data/game_model.json', encoding='utf-8')))
count = 0
for code, ev in model.events.items():
    parsed = parse_options(ev['text'])
    if parsed is None:
        continue
    headers, rows, note = parsed
    if len(headers) < 3:
        count += 1
        if count <= 20:
            print(code, 'headers=', headers, 'rows=', len(rows))
print('events with <3 parsed headers:', count, 'of', len(model.events))

