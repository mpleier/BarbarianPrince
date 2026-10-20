"""Compare the bot's actual camp against the camp DP, day by day.

Records, for every campaign:
  * the day the party first stands on its chosen ruin,
  * how many ruin days it actually digs,
  * the day it first reaches a temple and the gold it arrives with,
  * the DP's P(win) at that moment versus the DP's P(win) if it had
    followed the ruin-stopping policy exactly.
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

    ruin_day = None
    ruin_days = 0
    temple_day = None
    temple_gold = None
    temple_days = 0
    camp_days = 0
    actions = Counter()
    waste = 0

    def chooser(prompt):
        nonlocal ruin_day, ruin_days, temple_day, temple_gold
        nonlocal temple_days, camp_days, waste
        idx = b.choose(prompt)
        title = prompt.get('title', '')
        if 'action in hex' in title.lower():
            kind = g.place_kind(g.hex) or 'open'
            label = (prompt.get('options') or [{}])[idx].get('label', '')
            low = label.lower()
            if kind == 'ruins':
                if ruin_day is None:
                    ruin_day = g.day
                ruin_days += 1
                if 'search' not in low:
                    waste += 1
            elif kind == 'temple':
                if temple_day is None:
                    temple_day = g.day
                    temple_gold = g.gold
                    camp_days = 70 - g.day + 1
                temple_days += 1
                if 'offering' in low:
                    actions['offer'] += 1
                elif 'news' in low:
                    actions['news'] += 1
                elif 'rest' in low:
                    actions['rest'] += 1
                else:
                    actions['other'] += 1
        return idx

    g.run_until_idle(max_steps=6000, chooser=chooser)
    return dict(win=bool(g.staff),
                theory=ruin_value(max(0, 70 - int(to_ruin)), 0, to_temple),
                to_ruin=to_ruin, to_temple=to_temple, ruin_day=ruin_day,
                ruin_days=ruin_days, temple_day=temple_day,
                temple_gold=temple_gold or 0, temple_days=temple_days,
                camp_days=camp_days, actions=actions, waste=waste,
                camp_val=camp_value(camp_days, temple_gold or 0, 0, 0, 0, False))


def main(n, strategy='balanced'):
    rows = [r for r in (run(s, strategy) for s in range(1, n + 1)) if r]
    wins = sum(1 for r in rows if r['win'])
    print(f'{n} campaigns  win {wins / len(rows):.4f}')
    print(f'avg DP theory                {sum(r["theory"] for r in rows) / len(rows):.4f}')
    print(f'avg camp DP value at arrival {sum(r["camp_val"] for r in rows) / len(rows):.4f}')
    print(f'avg day first ruin reached   {sum(r["ruin_day"] or 0 for r in rows) / len(rows):.1f}')
    print(f'avg ruin days dug            {sum(r["ruin_days"] for r in rows) / len(rows):.1f}')
    print(f'avg day first temple         {sum(r["temple_day"] or 0 for r in rows) / len(rows):.1f}')
    print(f'avg camp days available      {sum(r["camp_days"] for r in rows) / len(rows):.1f}')
    print(f'avg temple days spent        {sum(r["temple_days"] for r in rows) / len(rows):.1f}')
    print(f'avg gold at temple           {sum(r["temple_gold"] for r in rows) / len(rows):.1f}')
    print(f'ruin days not spent searching: {sum(r["waste"] for r in rows)}')
    total = Counter()
    for r in rows:
        total.update(r['actions'])
    print('camp actions:', dict(total))
    broke = sum(1 for r in rows if r['temple_gold'] < 10)
    print(f'arrives with <10 gold: {broke} ({100.0 * broke / len(rows):.1f}%)')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200,
         sys.argv[2] if len(sys.argv) > 2 else 'balanced')
