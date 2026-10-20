"""What the bot actually looks like when it first reaches a temple.

The camp grid (_refs/camp_grid.py) says P(win) is a function of (camp days
left, gold on arrival).  This script measures where real campaigns land on
that grid, so the macro plan can be tuned against it.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot


def trace(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    first = None
    while not g.game_over:
        g.advance()
        if not g.prompts:
            break
        p = g.current()
        idx = b.choose(p)
        if first is None and g.place_kind(g.hex) == 'temple' \
                and 'action in hex' in p.get('title', ''):
            first = (g.day, g.gold, g.hex)
        g.answer(idx)
    return first, g.staff, g.day, g.gold


if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    rows = []
    for seed in range(1, N + 1):
        first, win, end_day, end_gold = trace(seed)
        rows.append((first, win, end_day, end_gold))

    reached = [r for r in rows if r[0]]
    print(f'{len(reached)}/{N} campaigns reach a temple')
    days = [r[0][0] for r in reached]
    gold = [r[0][1] for r in reached]
    left = [70 - d for d in days]
    print(f'arrival day  mean {sum(days)/len(days):.1f}  '
          f'median {sorted(days)[len(days)//2]}')
    print(f'gold on arr  mean {sum(gold)/len(gold):.1f}  '
          f'median {sorted(gold)[len(gold)//2]}  '
          f'max {max(gold)}  zero {sum(1 for x in gold if x < 10)}')
    print(f'camp days    mean {sum(left)/len(left):.1f}')

    buckets = {}
    for (d, gd, h), win, ed, eg in reached:
        key = (min(49, max(0, 70 - d) // 10) * 10, min(400, gd // 50) * 50)
        buckets.setdefault(key, [0, 0])
        buckets[key][0] += win
        buckets[key][1] += 1
    print('\ncamp-days bucket  gold bucket   win  n')
    for (c, gd), (w, n) in sorted(buckets.items()):
        if n >= 3:
            print(f'{c:>15}  {gd:>11}  {w/n:.3f}  {n}')
