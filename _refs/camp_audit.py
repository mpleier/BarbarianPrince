"""Audit the camp phase: does the bot's daily temple action match camp_dp?

For every day spent on a temple hex we record the DP's recommendation and the
option the bot actually picked from the daily menu, then report the mismatch
rate and the win probability the DP predicts for the positions reached.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot
from camp_dp import camp_action, camp_value


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    rows = []
    orig_menu = g.daily_menu
    orig_choose = b.choose

    def menu():
        if g.place_kind(g.hex) == 'temple' and not g.staff:
            plan = b.camp_plan()
            val = camp_value(b.camp_days_left(), g.gold, g.offering_bonus,
                             g.omen_bonus, g.influence_bonus, g.wit >= 5)
            rows.append([g.day, g.gold, plan, val, None,
                         any(c.wounds > 0 for c in g.living()), len(g.living())])
        return orig_menu()

    def choose(prompt, record=True):
        idx = orig_choose(prompt, record)
        if rows and 'action in hex' in prompt.get('title', '').lower():
            rows[-1][4] = prompt['options'][idx]['label'].lower()
        return idx

    g.daily_menu = menu
    b.choose = choose
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    return rows, g.staff


def main(n):
    total = mismatch = 0
    exp = 0.0
    wins = 0
    examples = []
    counts = {}
    for s in range(1, n + 1):
        rows, win = run(s)
        wins += win
        for day, gold, plan, val, label, hurt, size in rows:
            total += 1
            exp += val
            counts[label] = counts.get(label, 0) + 1
            if isinstance(plan, int):
                ok = f'offering' in (label or '')
            elif plan == 'news':
                ok = 'news' in (label or '')
            else:
                ok = 'rest' in (label or '')
            if not ok:
                mismatch += 1
                if len(examples) < 20:
                    examples.append((day, gold, plan, label, hurt, size))
    print(f'{n} campaigns, {total} temple days')
    print(f'  action mix: {counts}')
    print(f'  DP mismatches: {mismatch} ({mismatch/total:.1%})')
    print(f'  mean DP win chance at the start of a temple day: {exp/total:.4f}')
    print(f'  actual wins: {wins}/{n} = {wins/n:.3f}')
    for e in examples:
        print('   ', e)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)


