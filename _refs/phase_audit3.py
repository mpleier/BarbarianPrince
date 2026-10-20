"""Day-by-day campaign profiler: where the 70 days actually go.

Records every daily-menu choice so the ruin/travel/camp split, the camp action
mix and the days the bot throws away can be measured against the camp DP.
"""
import sys
sys.path.insert(0, 'src')

from collections import Counter

from engine import Game
from autoplay import Bot


def action_of(label):
    low = label.lower()
    if 'offering' in low:
        return 'offering'
    if 'ruin' in low:
        return 'ruins'
    if 'news' in low:
        return 'news'
    if 'rest' in low:
        return 'rest'
    if 'stop travelling' in low:
        return 'stop'
    if 'travel' in low:
        return 'travel'
    if 'end the day' in low:
        return 'end'
    if 'hire' in low:
        return 'hire'
    return 'other'


def run(seed, strategy='balanced'):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    days = []

    def chooser(prompt):
        idx = b.choose(prompt)
        if 'action in hex' in prompt.get('title', '').lower():
            kind = g.place_kind(g.hex) or 'open'
            label = (prompt.get('options') or [{}])[idx].get('label', '')
            days.append((g.day, kind, action_of(label), g.gold,
                         b.camp_days_left(),
                         b.camp_plan() if kind == 'temple' else None,
                         b.mining()))
        return idx

    g.run_until_idle(max_steps=6000, chooser=chooser)
    return g, b, days


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'
    wins = 0
    ruin_days = travel_days = temple_days = 0
    arrival_gold, arrival_day, camp_days_used, camp_days_avail = [], [], [], []
    camp_actions = Counter()
    days_after_temple = 0
    end_gold = []
    for seed in range(1, n + 1):
        g, b, days = run(seed, strategy)
        if g.staff:
            wins += 1
        arrived = False
        t_used = 0
        for day, kind, act, gold, avail, plan, mining in days:
            if kind == 'ruins':
                ruin_days += 1
            elif kind == 'temple':
                temple_days += 1
                t_used += 1
                camp_actions[act] += 1
                if not arrived:
                    arrived = True
                    arrival_gold.append(gold)
                    arrival_day.append(day)
                    camp_days_avail.append(avail)
            else:
                if arrived:
                    days_after_temple += 1
                travel_days += 1
        camp_days_used.append(t_used)
        end_gold.append(g.gold)
    print(f'seeds {n}  win rate {wins / n:.3f}')
    print(f'avg ruin days            {ruin_days / n:6.1f}')
    print(f'avg travel/other days    {travel_days / n:6.1f}')
    print(f'avg temple days          {temple_days / n:6.1f}')
    print(f'avg gold at first temple {sum(arrival_gold) / len(arrival_gold):.1f}')
    print(f'avg day of first temple  {sum(arrival_day) / len(arrival_day):.1f}')
    print(f'avg camp days available  {sum(camp_days_avail) / len(camp_days_avail):.1f}')
    print(f'avg camp days used       {sum(camp_days_used) / len(camp_days_used):.1f}')
    print(f'avg days after first temple: {days_after_temple / n:.1f}')
    print('camp action mix:', dict(camp_actions))
    print(f'avg final gold {sum(end_gold) / len(end_gold):.1f}')


if __name__ == '__main__':
    main()
