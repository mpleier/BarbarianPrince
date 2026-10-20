import sys
sys.path.insert(0, 'src')
from engine import Game

g = Game(seed=42)
for step in range(12):
    p = g.prompt()
    if p['kind'] == 'action':
        print(f"day {g.day} hex {g.hex} gold {g.gold} place {g.place_kind(g.hex)}")
        for o in p['options']:
            print('   ', o['label'], '|', o.get('handler_key'))
        break
