"""Where the 70 days actually go, and what the camp DP says about each day."""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot, TOTAL_DAYS
import camp_dp


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    phases = {'travel': 0, 'ruins': 0, 'temple': 0, 'other': 0}
    camp_days = 0
    orig = g.daily_menu

    def wrapped():
        k = g.place_kind(g.hex)
        if k == 'ruins':
            phases['ruins'] += 1
        elif k == 'temple':
            phases['temple'] += 1
        else:
            phases['other'] += 1
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    # 'other' days are mostly travel days
    return phases, g.staff, g.gold


def main(n):
    tot = {'travel': 0, 'ruins': 0, 'temple': 0, 'other': 0}
    wins = 0
    gold = 0
    for s in range(1, n + 1):
        ph, w, gd = run(s)
        for k in tot:
            tot[k] += ph[k]
        wins += w
        gold += gd
    print(f'{n} campaigns')
    for k, v in tot.items():
        print(f'  {k:8s} {v/n:6.1f} days')
    print(f'  wins {wins}/{n} = {wins/n:.1%}, avg final gold {gold/n:.1f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
