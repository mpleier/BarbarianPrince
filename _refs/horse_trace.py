"""Trace one campaign's travel decisions to see why the horse dealer never
appears: gold, goal, wants_horse() and the option the bot picked each day."""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    orig_menu = g.daily_menu
    orig_choose = b.choose

    def menu():
        plan = b.plan()
        print(f'd{g.day:>3} {g.hex} {str(g.place_kind(g.hex)):<8} gold {g.gold:>4} '
              f'speed {g.speed()} wants_horse {b.wants_horse()} '
              f'goal {b.goal_hex()} plan {plan}')
        return orig_menu()

    def choose(prompt):
        idx = orig_choose(prompt)
        if 'action in hex' in prompt.get('title', '').lower():
            print('      ->', prompt['options'][idx]['label'])
        elif prompt.get('title', '').startswith('Move'):
            print('      ->', prompt['options'][idx]['label'])
        return idx

    g.daily_menu = menu
    b.choose = choose
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    print('result:', 'WIN' if g.staff else 'loss', 'day', g.day, 'gold', g.gold)


if __name__ == '__main__':
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
