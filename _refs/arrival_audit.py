"""Compare the DP's predicted win chance at first arrival at a temple with the
campaign's actual outcome, and break the loss down by cause.

If the DP says 0.25 on arrival but the bot wins 0.19, the missing 6 points are
leaking somewhere between the ruin and the camp: encounters, follower upkeep,
travel days, or camp actions the DP does not model.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot
from camp_dp import camp_value


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    first = None
    orig_menu = g.daily_menu

    def menu():
        nonlocal first
        if first is None and g.place_kind(g.hex) == 'temple' and not g.staff \
                and b.camping():
            first = (g.day, g.gold, g.offering_bonus, g.omen_bonus,
                     g.influence_bonus, g.wit >= 5, len(g.living()))
        return orig_menu()

    g.daily_menu = menu
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    return first, g.staff, g.day, g.gold, len(g.living())


def main(n):
    tot_pred = 0.0
    wins = 0
    no_temple = 0
    rows = []
    for s in range(1, n + 1):
        first, win, end_day, end_gold, size = run(s)
        if first is None:
            no_temple += 1
            rows.append((0.0, 0, s))
            continue
        day, gold, perm, omen, inf, wit, party = first
        pred = camp_value(max(1, 70 - day + 1), gold, perm, omen, inf, wit)
        tot_pred += pred
        wins += win
        rows.append((pred, win, s))
    print(f'{n} campaigns: {no_temple} never reached a temple')
    print(f'  predicted win rate at first temple arrival: {tot_pred/n:.4f}')
    print(f'  actual win rate: {wins/n:.4f}')
    # bucket by prediction
    buckets = {}
    for pred, win, s in rows:
        key = int(pred * 10)
        b = buckets.setdefault(key, [0, 0])
        b[0] += 1
        b[1] += win
    print('  pred bucket | campaigns | actual wins')
    for k in sorted(buckets):
        c, w = buckets[k]
        print(f'   {k/10:.1f}-{(k+1)/10:.1f}  {c:>6}  {w/c:.3f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
