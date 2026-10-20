"""How often does the bot actually get a mount, and when?

r210 puts a horse dealer in front of the party on a hire roll of 5 or 10, and
r204a doubles the daily move only when *every* survivor is mounted.  This counts
the campaigns that end mounted, the day the mount was bought, and the gold it
cost - the numbers needed to decide whether the town detour in `_move` is worth
its days.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    mounted_day = None
    orig_menu = g.daily_menu

    def menu():
        nonlocal mounted_day
        if mounted_day is None and g.speed() >= 2:
            mounted_day = g.day
        return orig_menu()

    g.daily_menu = menu
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    return mounted_day, g.speed(), g.staff, g.day


def main(n):
    mounted = 0
    days = []
    wins_mounted = wins_unmounted = 0
    n_mounted = n_unmounted = 0
    for s in range(1, n + 1):
        day, speed, win, end = run(s)
        if speed >= 2:
            mounted += 1
            days.append(day)
            wins_mounted += win
            n_mounted += 1
        else:
            wins_unmounted += win
            n_unmounted += 1
    print(f'{n} campaigns: {mounted} ended mounted ({mounted/n:.1%})')
    if days:
        print(f'  mounted on average day {sum(days)/len(days):.1f}')
    print(f'  win rate mounted   : {wins_mounted/max(1,n_mounted):.3f}')
    print(f'  win rate unmounted : {wins_unmounted/max(1,n_unmounted):.3f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
