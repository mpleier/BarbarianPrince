"""Where the bot actually loses against the DP.

For every campaign we snapshot the state at the moment the party first
reaches its chosen ruin, and at the moment it first reaches its chosen
temple, and compare the DP's value with the outcome.  That isolates the
two places a campaign can go wrong: the ruin never produces enough gold,
or the temple stay is broken up by travel.
"""
import sys
sys.path.insert(0, 'src')

from collections import Counter

from engine import Game
from autoplay import Bot
from camp_dp import camp_value, ruin_value, ruin_gold_target


def run(seed, strategy='balanced'):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    plan = b.plan()
    if not plan:
        return None
    _, ruin, temple = plan
    to_ruin = b.travel_days(ruin).get(g.hex, 999.0)
    to_temple = b.travel_days(temple).get(ruin, 999.0)

    ruin_day = None
    runs = []
    cur = None

    def chooser(prompt):
        nonlocal ruin_day, cur
        idx = b.choose(prompt)
        if 'action in hex' in prompt.get('title', '').lower():
            kind = g.place_kind(g.hex)
            if g.hex == ruin and ruin_day is None:
                ruin_day = g.day
            if kind == 'temple':
                if cur and cur[1] == g.hex:
                    cur[2] += 1
                else:
                    cur = [g.day, g.hex, 1, g.gold]
                    runs.append(cur)
            else:
                cur = None
        return idx

    g.run_until_idle(max_steps=6000, chooser=chooser)
    first = runs[0] if runs else None
    return dict(win=bool(g.staff), ruin_day=ruin_day,
                visits=len(runs), max_run=max((r[2] for r in runs), default=0),
                camp_days=first[2] if first else 0,
                camp_gold=first[3] if first else 0,
                camp_day=first[0] if first else 0,
                theory=ruin_value(max(0, 70 - int(to_ruin)), 0, to_temple),
                target=ruin_gold_target(max(0, 70 - int(to_ruin)), to_temple),
                camp_val=camp_value(first[2], first[3], 0, 0, 0, False) if first else 0.0,
                to_ruin=to_ruin, to_temple=to_temple)


def main(n, strategy='balanced'):
    rows = [r for r in (run(s, strategy) for s in range(1, n + 1)) if r]
    wins = sum(1 for r in rows if r['win'])
    print(f'{n} campaigns  win {wins / len(rows):.4f}')
    print(f'DP theory at start      {sum(r["theory"] for r in rows) / len(rows):.4f}')
    print(f'DP gold target at ruin  {sum(r["target"] for r in rows) / len(rows):.1f}')
    print(f'avg day ruin reached    {sum(r["ruin_day"] or 0 for r in rows) / len(rows):.1f}')
    print(f'avg day camp started    {sum(r["camp_day"] for r in rows) / len(rows):.1f}')
    print(f'avg camp days           {sum(r["camp_days"] for r in rows) / len(rows):.1f}')
    print(f'avg camp gold           {sum(r["camp_gold"] for r in rows) / len(rows):.1f}')
    print(f'avg temple visits       {sum(r["visits"] for r in rows) / len(rows):.2f}')
    print('temple visit counts:', dict(sorted(Counter(r['visits'] for r in rows).items())))
    buckets = {}
    for r in rows:
        key = min(r['max_run'] // 5 * 5, 40)
        b = buckets.setdefault(key, [0, 0, 0.0])
        b[0] += 1
        b[1] += 1 if r['win'] else 0
        b[2] += r['camp_val']
    for k in sorted(buckets):
        c, w, v = buckets[k]
        print(f'  camp {k:2}-{k + 4:2}: n={c:4} win {w / c:.3f}  DP {v / c:.3f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300,
         sys.argv[2] if len(sys.argv) > 2 else 'balanced')
