"""Compare what the bot actually achieves with what the camp DP says is possible.

For every campaign we record the moment the party first reaches a temple, the
gold it carries, the number of temple days that remain, and then evaluate the
exact camp DP at that state.  The gap between the DP value and the realised win
rate is the headroom left in the camp phase itself.
"""
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '_refs')
sys.stdout.reconfigure(encoding='utf-8')

from engine import Game
from autoplay import Bot, TOTAL_DAYS
from camp_dp_exact import value as camp_value


def run(seed, strategy='balanced'):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    first_temple = None
    gold_at_temple = 0
    temple_days = 0
    orig = g.daily_menu

    def wrapped():
        nonlocal first_temple, gold_at_temple, temple_days
        if g.place_kind(g.hex) == 'temple' and not g.staff:
            if first_temple is None:
                first_temple = g.day
                gold_at_temple = g.gold
            temple_days += 1
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    return g, first_temple, gold_at_temple, temple_days


def main(n=300):
    strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'
    rows = []
    for s in range(1, n + 1):
        g, ft, gold, td = run(s, strategy)
        rows.append((ft or 0, gold, td, g.staff, g.gold))

    wins = sum(1 for r in rows if r[3])
    dp_total = 0.0
    for ft, gold, td, won, final in rows:
        dp_total += camp_value(td, gold, 0, 0, 0)

    print(f'{n} campaigns {strategy}: actual win {wins / n:.3f}, '
          f'camp-DP expected win {dp_total / n:.3f}')
    print(f'avg first temple day {sum(r[0] for r in rows) / n:.1f}')
    print(f'avg gold on arrival {sum(r[1] for r in rows) / n:.1f}')
    print(f'avg temple days {sum(r[2] for r in rows) / n:.1f}')
    print(f'avg final gold {sum(r[4] for r in rows) / n:.1f}')

    buckets = {}
    for ft, gold, td, won, final in rows:
        key = (min(td, 40) // 10 * 10, min(gold, 200) // 50 * 50)
        buckets.setdefault(key, []).append(won)
    print('\n  camp_days  gold   n   DP P(win)   actual')
    for (c, gld), vals in sorted(buckets.items()):
        if len(vals) < 5:
            continue
        print(f'  {c:>9} {gld:>5} {len(vals):>3}   '
              f'{camp_value(c, gld, 0, 0, 0):.3f}    {sum(vals) / len(vals):.3f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
