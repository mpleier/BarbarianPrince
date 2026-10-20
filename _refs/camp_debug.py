import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot
from camp_dp import camp_action

g = Game(seed=1)
b = Bot(g, 'balanced')
orig = g.daily_menu


def menu():
    orig()
    if g.place_kind(g.hex) == 'temple' and not g.staff and g.prompts:
        p = g.prompts[0]
        plan = b.camp_plan()
        if plan == 'news':
            print('day', g.day, 'gold', g.gold, 'perm', g.offering_bonus,
                'wounded', any(c.wounds > 0 for c in g.living()),
                'camping', b.camping())
            idx = b.choose(p)
            print('  options:', [o['label'] for o in p['options']])
            print('  chose  :', p['options'][idx]['label'])
    return None


g.daily_menu = menu
g.run_until_idle(max_steps=6000, chooser=b.choose)
print('win', g.staff)
