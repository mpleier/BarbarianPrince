"""Measure the *final* camp of each campaign against the camp DP.

The camp that matters is the last contiguous stay at a temple: the bot may
pass through temples on the way to its ruin.  For that stay we record the
gold and modifiers at the moment camping starts and compare the DP's P(win)
with the outcome.
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

    stay = None          # (start_day, gold, perm, omen, infl) of current stay
    best = None          # longest stay seen
    prev_day = None
    prev_temple = None

    def chooser(prompt):
        nonlocal stay, best, prev_day, prev_temple
        idx = b.choose(prompt)
        if 'action in hex' in prompt.get('title', '').lower():
            kind = g.place_kind(g.hex)
            if kind == 'temple' and b.camping():
                if prev_temple == g.hex and prev_day == g.day - 1:
                    stay = (stay[0], stay[1], stay[2], stay[3], stay[4],
                            stay[5] + 1)
                else:
                    stay = (g.day, g.gold, g.offering_bonus, g.omen_bonus,
                           g.influence_bonus, 1)
                if best is None or stay[5] > best[5]:
                    best = stay
                prev_temple, prev_day = g.hex, g.day
            else:
                prev_temple, prev_day = None, None
        return idx

    g.run_until_idle(max_steps=6000, chooser=chooser)
    return dict(win=bool(g.staff), theory=ruin_value(max(0, 70 - int(to_ruin)),
                                                    0, to_temple),
                to_ruin=to_ruin, to_temple=to_temple, stay=best,
                camp_val=camp_value(best[5], best[1], best[2], best[3],
                                    best[4], False) if best else 0.0)


def main(n, strategy='balanced'):
    rows = [r for r in (run(s, strategy) for s in range(1, n + 1)) if r]
    wins = sum(1 for r in rows if r['win'])
    print(f'{n} campaigns  win {wins / len(rows):.4f}')
    print(f'avg DP theory at start     {sum(r["theory"] for r in rows) / len(rows):.4f}')
    print(f'avg DP value of final camp {sum(r["camp_val"] for r in rows) / len(rows):.4f}')
    no_camp = sum(1 for r in rows if not r['stay'])
    print(f'campaigns with no camp: {no_camp}')
    hist = Counter()
    for r in rows:
        if r['stay']:
            hist[r['stay'][5]] += 1
    print('camp length distribution:', dict(sorted(hist.items())))
    gold_hist = Counter()
    for r in rows:
        if r['stay']:
            gold_hist[min(r['stay'][1] // 50 * 50, 500)] += 1
    print('camp start gold:', dict(sorted(gold_hist.items())))
    # per camp-length bucket: DP value vs actual
    buckets = {}
    for r in rows:
        if r['stay']:
            buckets.setdefault(r['stay'][5], [0, 0, 0.0])
            b = buckets[r['stay'][5]]
            b[0] += 1
            b[1] += 1 if r['win'] else 0
            b[2] += r['camp_val']
    for d, (c, w, v) in sorted(buckets.items()):
        print(f'  camp days {d:2}: n={c:4} win {w / c:.3f}  DP {v / c:.3f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300,
         sys.argv[2] if len(sys.argv) > 2 else 'balanced')
