"""Empirical comparison of temple-camping policies.

Every campaign starts parked at a temple with a fixed pile of gold, so the
number is purely the quality of the r212 strategy.  The engine treats the
r212 "magnificent error" (total 2) and "High Priest insulted" (total 5)
results as flavour text only, so a 1-gold offering has no downside beyond
the gold it costs.

Policies:
  one    always offer 1 gold
  ten    offer 10 whenever affordable
  smart  offer 10 only when a +1/+3 modifier is already in play
  newsN  seek news (r209) up to N times while gold is plentiful, then smart
  dp     exact camp DP (news disabled)
  dpn    exact camp DP (news enabled)
"""
import re
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '_refs')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot
from camp_dp_exact import best_action

N_POLICIES = ('one', 'ten', 'smart', 'news2', 'news4', 'news8', 'dp', 'dpn',
              'hyb', 'hyb2', 'hybnews', 'bot')


def temple_of(g):
    temples = [h for h, p in g.features['places'].items() if p['kind'] == 'temple']
    return min(temples) if temples else None


def choose(g, name):
    p = g.current()
    title = p.get('title', '').lower()
    labels = [o['label'].lower() for o in p['options']]

    if 'action in hex' in title:
        if name in ('one', 'ten', 'smart'):
            for i, l in enumerate(labels):
                if 'offering' in l:
                    return i
            return next((i for i, l in enumerate(labels) if 'end the day' in l), 0)
        if name in ('hyb', 'hyb2', 'hybnews'):
            days = max(1, 71 - g.day)
            surplus = g.gold - (10 * days if name != 'hyb2' else 10 * days - 3)
            if (name == 'hybnews' and surplus >= 40 and not g.offering_bonus
                    and getattr(g, '_news_tries', 0) < 3):
                g._news_tries = getattr(g, '_news_tries', 0) + 1
                for i, l in enumerate(labels):
                    if 'news' in l:
                        return i
            for i, l in enumerate(labels):
                if 'offering' in l:
                    return i
            return next((i for i, l in enumerate(labels) if 'end the day' in l), 0)
        if name == 'bot':
            return Bot(g, 'balanced').choose(p)
        if name.startswith('news'):
            limit = int(name[4:])
            tries = getattr(g, '_news_tries', 0)
            if tries < limit and not g.offering_bonus and g.gold >= 60:
                g._news_tries = tries + 1
                for i, l in enumerate(labels):
                    if 'news' in l:
                        return i
            for i, l in enumerate(labels):
                if 'offering' in l:
                    return i
            return next((i for i, l in enumerate(labels) if 'end the day' in l), 0)
        if name in ('dp', 'dpn'):
            days = max(1, 71 - g.day)
            act, _ = best_action(days, min(g.gold, 400), g.offering_bonus,
                                 g.omen_bonus, g.influence_bonus, g.wit >= 5)
            if act == 'news' and name == 'dpn':
                for i, l in enumerate(labels):
                    if 'news' in l:
                        return i
            if isinstance(act, int):
                for i, l in enumerate(labels):
                    # the daily menu says "Make an offering", not "offer N gold"
                    if 'offering' in l:
                        return i
            return next((i for i, l in enumerate(labels) if 'end the day' in l), 0)
        return 0

    if 'offering' in title and any('offer ' in l for l in labels):
        afford = []
        for i, l in enumerate(labels):
            m = re.search(r'offer (\d+) gold', l)
            if m and int(m.group(1)) <= g.gold:
                afford.append((i, int(m.group(1))))
        if not afford:
            return next((i for i, l in enumerate(labels) if 'withdraw' in l), 0)
        if name == 'ten':
            if g.gold >= 12:
                hit = [i for i, a in afford if a == 10]
                if hit:
                    return hit[0]
            return min(afford, key=lambda x: x[1])[0]
        if name == 'one':
            return min(afford, key=lambda x: x[1])[0]
        if name in ('hyb', 'hyb2', 'hybnews'):
            days = max(1, 71 - g.day)
            threshold = 10 * days if name == 'hyb' else 10 * days - 3
            bonus = g.offering_bonus + g.omen_bonus + g.influence_bonus
            if (g.gold >= threshold or bonus) and g.gold >= 10:
                hit = [i for i, a in afford if a == 10]
                if hit:
                    return hit[0]
            return min(afford, key=lambda x: x[1])[0]
        if name == 'smart' or name.startswith('news'):
            bonus = g.offering_bonus + g.omen_bonus + g.influence_bonus
            if bonus and g.gold >= 11:
                hit = [i for i, a in afford if a == 10]
                if hit:
                    return hit[0]
            return min(afford, key=lambda x: x[1])[0]
        if name in ('dp', 'dpn'):
            days = max(1, 71 - g.day)
            act, _ = best_action(days, min(g.gold, 400), g.offering_bonus,
                                 g.omen_bonus, g.influence_bonus, g.wit >= 5)
            if isinstance(act, int):
                hit = [i for i, a in afford if a == act]
                if hit:
                    return hit[0]
            return min(afford, key=lambda x: x[1])[0]
        return 0

    if 'high priest' in title:
        for i, l in enumerate(labels):
            if 'influence' in l:
                return i
        return 0

    if 'meal' in title:
        for i, l in enumerate(labels):
            if 'hungry' in l:
                return i
        return 0
    if 'lodging' in title:
        return 1 if len(p['options']) > 1 else 0
    return 0


def run(seed, name, gold, day):
    g = Game(seed=seed)
    g.gold = gold
    g.day = day
    g.hex = temple_of(g)
    if g.hex is None:
        return False
    g.run_until_idle(max_steps=8000, chooser=lambda p: choose(g, name))
    return g.staff


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    policies = sys.argv[2].split(',') if len(sys.argv) > 2 else list(N_POLICIES)
    days = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else (31, 41, 51)
    golds = [int(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else (60, 100, 200, 400)
    for day in days:
        for gold in golds:
            line = []
            for name in policies:
                w = sum(run(s, name, gold, day) for s in range(1, n + 1))
                line.append(f'{name:<6}{w / n:.3f}')
            print(f'C={71-day:>2} G={gold:>3}  ' + '  '.join(line))
        print()
