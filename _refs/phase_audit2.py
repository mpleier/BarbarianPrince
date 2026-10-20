"""Where the campaign's 70 days actually go.

For every campaign we record the plan the bot forms on day 1 (which ruin, which
temple) and then follow the party day by day, classifying each day as:

  approach  - travelling towards the planned ruin
  mine      - searching that ruin
  transit   - travelling from the ruin to the temple
  camp      - at the temple making an offering
  wander    - anywhere else / doing nothing useful

This is the diagnostic that tells us whether the bot is following the macro
plan or leaking days.
"""
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '_refs')

from engine import Game
from autoplay import Bot, TOTAL_DAYS


def classify(day, hex_, kind, window, plan, reached_ruin, reached_temple):
    low = [l.lower() for l in window]
    if any('searching the ruins' in l for l in low):
        return 'mine'
    if any('offering of' in l for l in low):
        return 'camp'
    if any('travel action' in l for l in low):
        return 'travel'
    return 'other'


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    plan = b.plan()
    days = []
    orig = g.daily_menu

    def wrapped():
        days.append((g.day, g.hex, g.place_kind(g.hex), g.gold, len(g.log)))
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    out = []
    for i, (day, hex_, kind, gold, log_end) in enumerate(days):
        nxt = days[i + 1][4] if i + 1 < len(days) else len(g.log)
        out.append((day, hex_, kind, gold, g.log[log_end:nxt]))
    return plan, out


def main(n=100):
    totals = {}
    reach_ruin = []
    reach_temple = []
    ruin_days = []
    idle_at_ruin = 0
    idle_at_temple = 0
    plan_days = []
    for s in range(1, n + 1):
        plan, days = run(s)
        counts = {}
        first_ruin = first_temple = None
        for day, hex_, kind, gold, window in days:
            c = classify(day, hex_, kind, window, plan, None, None)
            counts[c] = counts.get(c, 0) + 1
            if kind == 'ruins':
                if first_ruin is None:
                    first_ruin = day
                if c != 'mine':
                    idle_at_ruin += 1
            if kind == 'temple':
                if first_temple is None:
                    first_temple = day
                if c != 'camp':
                    idle_at_temple += 1
        for k, v in counts.items():
            totals[k] = totals.get(k, 0) + v
        if first_ruin:
            reach_ruin.append(first_ruin)
        if first_temple:
            reach_temple.append(first_temple)
        ruin_days.append(counts.get('mine', 0))
        if plan and first_temple:
            plan_days.append((plan[0], first_temple, counts.get('mine', 0),
                             counts.get('camp', 0)))
    print(f'{n} campaigns')
    for k in ('travel', 'mine', 'camp', 'other'):
        print(f'  {k:<8} {totals.get(k, 0) / n:6.1f} days')
    print(f'  first reached a ruins hex on day {sum(reach_ruin) / len(reach_ruin):.1f}')
    print(f'  first reached a temple on day {sum(reach_temple) / len(reach_temple):.1f}')
    print(f'  ruin-search days per campaign {sum(ruin_days) / n:.1f}')
    print(f'  days spent on a ruins hex without searching {idle_at_ruin / n:.1f}')
    print(f'  days spent on a temple hex without offering {idle_at_temple / n:.1f}')
    print(f'  campaigns that never reach a temple: {n - len(reach_temple)}')
    print('\n  plan camp_days  actual first temple  mined  camped')
    for p, ft, m, c in plan_days[:10]:
        print(f'  {p:>13} {ft:>18} {m:>6} {c:>6}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
