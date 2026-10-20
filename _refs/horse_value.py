"""Upper bound on the value of a mount: give the Prince a horse at the start.

r204a doubles the daily move when every survivor is mounted, so this measures
how much win rate a guaranteed mount is worth before the bot tries to buy one
through the r210 horse dealer.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game, Character
from autoplay import Bot


def run(seed, mounted):
    g = Game(seed=seed)
    if mounted:
        g.party[0].mount = 'horse'
    b = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    travel = sum(1 for line in g.log if 'Travel to a new hex' in line)
    return g.staff, g.day, g.gold, travel


def main(n):
    for mounted in (False, True):
        wins = 0
        days = []
        gold = []
        travel = []
        for s in range(1, n + 1):
            w, d, gd, t = run(s, mounted)
            wins += w
            days.append(d)
            gold.append(gd)
            travel.append(t)
        print(f'mounted={mounted!s:<5} wins {wins}/{n} = {wins/n:.3f}  '
              f'avg days {sum(days)/len(days):.1f}  avg gold {sum(gold)/len(gold):.1f}  '
              f'avg travel steps {sum(travel)/len(travel):.1f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
