import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot, HEX_RE, _p_lost

g = Game(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 1)
b = Bot(g, 'balanced')

def chooser(prompt):
    idx = b.choose(prompt)
    if 'Choose the next hex' in prompt.get('text', ''):
        goal = b.goal_hex()
        dgoal = b.travel_days(goal) if goal else {}
        here = dgoal.get(g.hex, 0.0)
        print(f'day {g.day:>2} hex {g.hex} gold {g.gold:>3} goal {goal} '
              f'here {here:.2f} chose {prompt["options"][idx]["label"]}')
        for o in prompt['options']:
            m = HEX_RE.search(o['label'])
            hid = m.group(1) if m else None
            if hid and hid in dgoal:
                step = 1.0 if '[road]' in o['label'] else 1.0 / (
                    1.0 - _p_lost(g.model.travel_terrain(g.hex)))
                print('    ', o['label'], 'gain',
                      round(here - (step + dgoal[hid]), 2))
    return idx

g.run_until_idle(max_steps=6000, chooser=chooser)
print('final: day', g.day, 'gold', g.gold, 'staff', g.staff, 'hex', g.hex)
print('path', ' '.join(b.path))

