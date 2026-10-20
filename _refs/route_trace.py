"""Print the day-by-day route and action for a handful of campaigns.

The macro plan is "walk to the best ruin, mine it, walk to the paired temple,
camp".  `action_audit` says the bot spends 23 of its 70 days walking, which is
far more than the ~10 expected days that plan implies.  This script shows the
actual sequence of hexes and actions so the detours are visible.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')

from engine import Game
from autoplay import Bot

seeds = [int(x) for x in sys.argv[1:]] or [1, 2, 3]

for seed in seeds:
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    plan = b.plan()
    rows = []
    orig = g.daily_menu

    def wrapped():
        orig()
        p = g.current()
        if p and 'action in hex' in p.get('title', '').lower():
            i = b.suggest(p)
            rows.append((g.day, g.hex, g.place_kind(g.hex), g.gold,
                         p['options'][i]['label'], b.goal_hex()))
        return None
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    print(f'--- seed {seed}: plan ruin {plan[1]} temple {plan[2]} '
          f'camp_days {plan[0]:.1f}')
    for day, hex_, kind, gold, act, goal in rows:
        print(f'  d{day:>2} {hex_} {str(kind):<7} gold {gold:>4}  {act:<26} '
            f'goal {goal}')
    print(f'  result: staff={g.staff} final gold={g.gold}')
    print()
