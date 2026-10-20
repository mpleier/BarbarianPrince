"""Measure the true cost of a day at a temple (r215 food + r217 lodging)."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game

for party in (1, 2, 4):
    for kind in ('temple', 'town', 'ruins', None):
        g = Game(seed=7)
        # find a hex of the wanted kind
        hexes = [h for h, p in g.features['places'].items() if p['kind'] == kind]
        g.hex = hexes[0] if hexes else '0101'
        g.visited.add(g.hex)
        g.gold = 200
        # grow the party
        from engine import Character
        for i in range(party - 1):
            g.party.append(Character(name=f'Man {i}', skill=4, endurance=5,
                                     wounds=0, mount='none'))
        g.action = 'skip'
        g.phase = 'endday'
        g.food_done = False
        before = g.gold
        while not g.game_over and g.phase == 'endday':
            g.advance()
            if g.prompts:
                p = g.prompts[0]
                # pick the cheapest sensible option
                idx = 0
                for i, o in enumerate(p['options']):
                    if 'eat' in o['label'].lower() or 'pay' in o['label'].lower():
                        idx = i
                        break
                g.answer(idx)
        print(f'{kind or "wilderness":<10} party {party}: gold {before} -> {g.gold} '
              f'(cost {before - g.gold})')
