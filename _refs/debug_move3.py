import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot


def choice(title, text, labels):
    return {'kind': 'choice', 'title': title, 'text': text,
            'options': [{'label': l, 'handler': (lambda: 'ok')} for l in labels]}


g = Game(seed=2)
g.moves_left = 0
b = Bot(g, 'balanced')
d = b.distances(g.hex)
goal = b.goal_hex()
print('hex', g.hex, 'moves_left', g.moves_left, 'goal', goal, 'camping', b.camping())
print('dist 0102', d.get('0102'), 'dist goal', d.get(goal))
opts = ['N -> 0102 (Farmland)', 'Stop travelling for the day']
print('chosen', opts[b.choose(choice('Move (0 hex(es) left)', 'In hex 0101.', opts))])
print('temples:', sorted(h for h, p in g.features['places'].items()
                         if p['kind'] == 'temple'))
print('kind 0101', g.place_kind('0101'), 'kind 0102', g.place_kind('0102'))
