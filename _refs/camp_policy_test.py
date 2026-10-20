"""Measure the win rate of alternative temple-camping policies.

Every campaign starts parked at a temple with a fixed pile of gold, so the
result is purely the quality of the r212 strategy.  r212: total = 2d6 +
(1 if the offering is 10+) + permanent news omen + yesterday's omen (a 7) +
High Priest influence (a 12/13).  14+ wins; 2 is death and 10 exiles the
party from that temple.
"""
import re
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot


def temple_of(g):
    temples = [h for h, p in g.features['places'].items() if p['kind'] == 'temple']
    return min(temples) if temples else None


def policy_choice(g, name):
    p = g.current()
    title = p.get('title', '').lower()
    labels = [o['label'].lower() for o in p['options']]

    if 'action in hex' in title:
        if name in ('camp', 'ten', 'one', 'smart'):
            for i, l in enumerate(labels):
                if 'offering' in l:
                    return i
            for i, l in enumerate(labels):
                if 'end the day' in l:
                    return i
            return 0
        if name == 'news':
            for i, l in enumerate(labels):
                if 'news' in l and g.gold >= 8:
                    return i
            for i, l in enumerate(labels):
                if 'offering' in l:
                    return i
            return 0
        return 0

    if 'offering' in title and any('offer ' in l for l in labels):
        amounts = []
        for i, l in enumerate(labels):
            m = re.search(r'offer (\d+) gold', l)
            if m:
                amounts.append((i, int(m.group(1))))
        if not amounts:
            return 0
        afford = [(i, a) for i, a in amounts if a <= g.gold]
        if not afford:
            return next((i for i, l in enumerate(labels) if 'withdraw' in l), 0)
        if name in ('ten', 'camp', 'news'):
            if g.gold >= 12:
                ten = [i for i, a in afford if a == 10]
                if ten:
                    return ten[0]
            return min(afford, key=lambda x: x[1])[0]
        if name == 'one':
            return min(afford, key=lambda x: x[1])[0]
        if name == 'smart':
            bonus = (1 if g.gold >= 10 else 0) + g.offering_bonus + g.omen_bonus \
                + g.influence_bonus
            if bonus + 12 >= 14 and g.gold >= 12:
                return next(i for i, a in afford if a == 10)
            return min(afford, key=lambda x: x[1])[0]
        return 0

    if 'high priest' in title:
        for i, l in enumerate(labels):
            if 'influence' in l:
                return i
        return 0

    return 0


def run(seed, name, gold, day):
    g = Game(seed=seed)
    g.gold = gold
    g.day = day
    g.hex = temple_of(g)
    if g.hex is None:
        return False, 0
    if name == 'bot':
        bot = Bot(g, 'balanced')
        g.run_until_idle(max_steps=6000, chooser=bot.choose)
    else:
        g.run_until_idle(max_steps=6000, chooser=lambda p: policy_choice(g, name))
    return g.staff, g.day


if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    for gold in (30, 60, 100, 200, 400):
        for name in ('bot', 'ten', 'one', 'smart', 'news'):
            wins = 0
            days = []
            for seed in range(1, N + 1):
                w, d = run(seed, name, gold, 31)
                if w:
                    wins += 1
                    days.append(d)
            print(f'{gold:>4} gold  {name:<6} win {wins / N:.3f}  '
                  f'mean win day {sum(days) / max(1, len(days)):.1f}')
        print()
