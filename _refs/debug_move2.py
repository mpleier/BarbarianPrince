import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=2)
g.moves_left = 0
b = Bot(g, 'balanced')
d = b.distances(g.hex)
goal = b.goal_hex()
print('hex', g.hex, 'moves_left', g.moves_left, 'goal', goal, 'camping', b.camping())
print('dist 0102', d.get('0102'), 'dist goal', d.get(goal))
opts = ['N -> 0102 (Farmland)', 'Stop travelling for the day']
print('chosen', opts[b.choose({'kind': 'choice', 'title': 'Move (0 hex(es) left)',
                               'text': 'In hex 0101.',
                               'options': [{'label': l, 'handler': (lambda: 'ok')}
                                          for l in opts]}])
print('temples:', sorted(h for h, p in g.features['places'].items()
                         if p['kind'] == 'temple'))
