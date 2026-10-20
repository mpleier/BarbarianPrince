"""How far is the bot's walking from the minimum-expected-days path?

For every travel day we compare the hex the bot steps into with the hex the
Dijkstra says is best, and report the extra expected days the detour costs.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot, HEX_RE


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    plan = b.plan()
    if not plan:
        return None
    _, ruin, temple = plan

    stats = dict(steps=0, detours=0, extra=0.0)
    orig_move = b._move

    def move(prompt, record):
        opts = prompt['options']
        goal = b.goal_hex()
        if goal is None:
            return orig_move(prompt, record)
        dist = b.travel_days(goal)
        best = None
        for i, o in enumerate(opts):
            m = HEX_RE.search(o['label'])
            if not m:
                continue
            score = dist.get(m.group(1), 999.0)
            if best is None or score < best[1] - 1e-9:
                best = (i, score, m.group(1))
        idx = orig_move(prompt, record)
        if best is not None:
            m = HEX_RE.search(opts[idx]['label'])
            if m:
                stats['steps'] += 1
                if m.group(1) != best[2]:
                    stats['detours'] += 1
                    stats['extra'] += dist.get(m.group(1), 999.0) - best[1]
        return idx

    b._move = move

    g.run_until_idle(max_steps=6000, chooser=b.choose)
    stats['win'] = g.staff
    stats['gold'] = g.gold
    return stats


def main(n):
    rows = [r for r in (run(s) for s in range(1, n + 1)) if r]
    steps = sum(r['steps'] for r in rows)
    detours = sum(r['detours'] for r in rows)
    extra = sum(r['extra'] for r in rows)
    print(f'{n} campaigns: {steps} travel steps, {detours} off-optimal '
          f'({100.0 * detours / steps:.1f}%), {extra:.1f} extra expected days '
          f'({extra / n:.2f} per campaign)')
    print(f'wins {sum(1 for r in rows if r["win"])}/{n}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)



def main(n):
    rows = [r for r in (run(s) for s in range(1, n + 1)) if r]
    steps = sum(r['steps'] for r in rows)
    detours = sum(r['detours'] for r in rows)
    extra = sum(r['extra'] for r in rows)
    print(f'{n} campaigns: {steps} travel steps, {detours} off-optimal '
          f'({100.0 * detours / steps:.1f}%), {extra:.1f} extra expected days '
          f'({extra / n:.2f} per campaign)')
    print(f'wins {sum(1 for r in rows if r["win"])}/{n}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
