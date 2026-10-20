"""Where the bot loses against the ruin/camp DP's own prediction.

For every campaign we compute the DP-optimal P(win) from the starting hex,
then compare it with what the bot actually achieves, breaking the shortfall
down into (a) travel to the ruin, (b) the mining phase, (c) the camp itself.
"""
import sys
sys.path.insert(0, 'src')

from collections import Counter

from engine import Game
from autoplay import Bot
from camp_dp import camp_value, ruin_value


def run(seed, strategy='balanced'):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    plan = b.plan()
    if not plan:
        return None
    _, ruin, temple = plan
    to_ruin = b.travel_days(ruin).get(g.hex, 999.0)
    to_temple = b.travel_days(temple).get(ruin, 999.0)
    theory = ruin_value(max(0, 70 - int(to_ruin)), 0, to_temple)

    first = None
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    return dict(win=bool(g.staff), reason=g.reason, day=g.day, gold=g.gold,
                theory=theory, to_ruin=to_ruin, to_temple=to_temple,
                ruin=ruin, temple=temple, first=first)


def main(n, strategy='balanced'):
    rows = []
    for s in range(1, n + 1):
        r = run(s, strategy)
        if r:
            rows.append(r)
    wins = sum(1 for r in rows if r['win'])
    theory = sum(r['theory'] for r in rows) / len(rows)
    print(f'{n} campaigns: actual {wins / len(rows):.4f}  '
          f'DP prediction {theory:.4f}  gap {theory - wins / len(rows):.4f}')
    print(f'avg travel to ruin {sum(r["to_ruin"] for r in rows) / len(rows):.1f} '
          f'avg ruin->temple {sum(r["to_temple"] for r in rows) / len(rows):.1f}')
    reasons = Counter(r['reason'] for r in rows)
    for reason, count in reasons.most_common():
        print(f'  {count:4}  {reason}')
    # distribution of final gold for the losses
    lost = [r for r in rows if not r['win']]
    hist = Counter()
    for r in lost:
        hist[min(r['gold'] // 50 * 50, 500)] += 1
    print('final gold of losses:', dict(sorted(hist.items())))


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200,
         sys.argv[2] if len(sys.argv) > 2 else 'balanced')
