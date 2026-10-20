"""Run the exact r212 camp DP inside the real engine.

`camp_dp_exact` models the camp analytically; this harness plays the same
policy through the engine so the model can be checked against the rules as
actually implemented (prison from r212 results 2 and 5, free lodging on a 6,
etc.).  It also isolates how much the news omen (r209 result 4) is worth.
"""
import re
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '_refs')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from camp_dp_exact import best_action


def temple_of(g):
    temples = [h for h, p in g.features['places'].items() if p['kind'] == 'temple']
    return min(temples) if temples else None


def dp_choice(g, use_news=True, skip_upkeep=True):
    """Play one prompt using the exact camp DP."""
    p = g.current()
    title = p.get('title', '').lower()
    labels = [o['label'].lower() for o in p['options']]

    if 'action in hex' in title:
        days = max(1, 71 - g.day)
        act, _ = best_action(days, min(g.gold, 400), g.offering_bonus,
                             g.omen_bonus, g.influence_bonus, g.wit >= 5)
        if act != 'rest':
            for i, l in enumerate(labels):
                if act == 'news' and 'news' in l:
                    return i
                if act == 'ruins' and 'ruins' in l:
                    return i
                # the daily menu labels offerings as "Make an offering"; the
                # gold amount is only chosen in the r212 prompt itself.
                if isinstance(act, int) and 'offering' in l:
                    return i
        for i, l in enumerate(labels):
            if 'end the day' in l:
                return i
        return 0

    if 'offering' in title and any('offer ' in l for l in labels):
        afford = []
        for i, l in enumerate(labels):
            m = re.search(r'offer (\d+) gold', l)
            if m and int(m.group(1)) <= g.gold:
                afford.append((i, int(m.group(1))))
        if not afford:
            return next((i for i, l in enumerate(labels) if 'withdraw' in l), 0)
        days = max(1, 71 - g.day)
        act, _ = best_action(days, min(g.gold, 400), g.offering_bonus,
                            g.omen_bonus, g.influence_bonus, g.wit >= 5)
        if isinstance(act, int):
            hit = [i for i, a in afford if a == act]
            if hit:
                return hit[0]
        return min(afford, key=lambda x: x[1])[0]

    if 'high priest' in title:
        for i, l in enumerate(labels):
            if 'influence' in l:
                return i
        return 0

    if 'meal' in title:
        if skip_upkeep:
            for i, l in enumerate(labels):
                if 'hungry' in l:
                    return i
        for i, l in enumerate(labels):
            if 'buy meals' in l and g.gold >= int(re.search(r'(\d+) gold', l).group(1)) + 3:
                return i
        return 0

    if 'lodging' in title:
        return 1 if skip_upkeep else 0

    return 0


def run(seed, gold, day, **kw):
    g = Game(seed=seed)
    g.gold = gold
    g.day = day
    g.hex = temple_of(g)
    if g.hex is None:
        return False, 0
    g.run_until_idle(max_steps=8000, chooser=lambda p: dp_choice(g, **kw))
    return g.staff, g.day


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    for day in (31, 41, 51):
        for gold in (60, 100, 200, 400):
            for upkeep in (True, False):
                wins = sum(run(s, gold, day, skip_upkeep=upkeep)[0]
                           for s in range(1, n + 1))
                print(f'C={70-day+1:>2} G={gold:>3} upkeep={int(upkeep)} '
                      f'win {wins / n:.3f}')
        print()
