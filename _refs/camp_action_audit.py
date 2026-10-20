"""Audit every camp day: what the DP recommends vs what the bot does.

Also records the state transitions so we can see how much of the DP's
predicted win chance is lost during the camp itself.
"""
import sys
sys.path.insert(0, 'src')

from collections import Counter

from engine import Game
from autoplay import Bot
from camp_dp import camp_action, camp_value


def run(seed, strategy='balanced'):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    rows = []
    drift = 0.0
    camp_days = 0

    def chooser(prompt):
        nonlocal drift, camp_days
        idx = b.choose(prompt)
        title = prompt.get('title', '').lower()
        if 'action in hex' in title and g.place_kind(g.hex) == 'temple' and b.camping():
            days = max(1, 70 - g.day + 1)
            gold = g.gold
            want = camp_action(days, gold, g.offering_bonus, g.omen_bonus,
                               g.influence_bonus, g.wit >= 5)
            got = prompt['options'][idx]['label'].lower()
            val = camp_value(days, gold, g.offering_bonus, g.omen_bonus,
                             g.influence_bonus, g.wit >= 5)
            rows.append((g.day, days, gold, want, got, val))
            camp_days += 1
            drift += val
        return idx

    g.run_until_idle(max_steps=6000, chooser=chooser)
    return rows, bool(g.staff), camp_days


def main(n, strategy='balanced'):
    mismatch = Counter()
    actions = Counter()
    wins = 0
    total_val = 0.0
    for s in range(1, n + 1):
        rows, win, cd = run(s, strategy)
        wins += 1 if win else 0
        if rows:
            total_val += rows[0][5]
        for d, days, gold, want, got, val in rows:
            actions[str(want)] += 1
            if want != 'rest' and 'offering' not in got:
                mismatch[(want, got[:20])] += 1
            if want == 'news' and 'news' not in got:
                mismatch[(want, got[:20])] += 1
            if want == 'rest' and 'rest' not in got and 'offering' in got:
                mismatch[(want, got[:20])] += 1
    print(f'{n} campaigns win {wins / n:.4f}  DP camp value {total_val / n:.4f}')
    print('DP actions:', dict(actions))
    print('mismatches:', dict(mismatch))


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300,
         sys.argv[2] if len(sys.argv) > 2 else 'balanced')
