"""How often is the party standing in a town with gold, and does it hire?

The horse dealer (r210) only appears when the party takes the 'seek to hire'
action in a town or castle and rolls 5 or 10.  This counts the opportunities
the bot actually gets and the ones it takes.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    town_days = []
    hires = 0
    orig_menu = g.daily_menu
    orig_choose = b.choose

    def menu():
        if g.place_kind(g.hex) in ('town', 'castle'):
            town_days.append((g.day, g.gold, g.speed(), b.wants_horse()))
        return orig_menu()

    def choose(prompt):
        nonlocal hires
        idx = orig_choose(prompt)
        if 'action in hex' in prompt.get('title', '').lower():
            if 'hire' in prompt['options'][idx]['label'].lower():
                hires += 1
        return idx

    g.daily_menu = menu
    b.choose = choose
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    return town_days, hires, g.staff


def main(n):
    town = 0
    gold_town = 0
    wants = 0
    hires = 0
    wins = 0
    for s in range(1, n + 1):
        td, h, w = run(s)
        town += len(td)
        gold_town += sum(1 for d, gold, sp, wh in td if gold >= 10)
        wants += sum(1 for d, gold, sp, wh in td if wh)
        hires += h
        wins += w
    print(f'{n} campaigns')
    print(f'  town/castle days      {town}  ({town/n:.1f} per campaign)')
    print(f'  of those, gold >= 10  {gold_town}')
    print(f'  wants_horse() true    {wants}')
    print(f'  hire actions taken    {hires}  ({hires/n:.2f} per campaign)')
    print(f'  wins                  {wins}/{n}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
