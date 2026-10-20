"""What happens at the first temple arrival: gold, party, camp days, DP value,
and how many camp days the bot actually spends offering.

The macro plan says the party should arrive with ~45 camp days left; the gap
between that and what really happens is where the win rate is lost.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot
from camp_dp import camp_value


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    first = []
    orig = g.daily_menu

    def menu():
        if (not first and g.place_kind(g.hex) == 'temple'
                and not g.staff and b.camping()):
            first.append((g.day, g.gold, len(g.living()), b.camp_days_left(),
                          b.camp_win_chance()))
        return orig()

    g.daily_menu = menu
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    camp_days = sum(1 for line in g.log
                    if 'Offering of' in line or 'Seek news' in line)
    return first, g.staff, g.day, camp_days


def main(n=200):
    rows = []
    for s in range(1, n + 1):
        first, win, end_day, camp_days = run(s)
        if not first:
            rows.append((0, 0, 0, 0, 0, bool(win), end_day, camp_days))
            continue
        d, gd, pc, cd, dp = first[0]
        rows.append((dp, d, gd, pc, cd, bool(win), end_day, camp_days))
    rows.sort()
    wins = sum(1 for r in rows if r[5])
    print(f'{n} campaigns, win rate {wins / n:.3f}')
    print(f'  avg arrival day   {sum(r[1] for r in rows) / n:.1f}')
    print(f'  avg gold at camp  {sum(r[2] for r in rows) / n:.1f}')
    print(f'  avg party at camp {sum(r[3] for r in rows) / n:.2f}')
    print(f'  avg camp days left{sum(r[4] for r in rows) / n:.1f}')
    print(f'  avg DP win chance {sum(r[0] for r in rows) / n:.3f}')
    print(f'  avg offering days {sum(r[7] for r in rows) / n:.1f}')
    print('  worst 5:')
    for r in rows[:5]:
        print('   ', r)
    print('  best 5:')
    for r in rows[-5:]:
        print('   ', r)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
