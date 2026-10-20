"""Validate the camp DP against the engine.

Drop a lone Prince on a temple with a given pile of gold and let the exact
camp DP run the days.  If the engine's camp matches camp_value() the two
numbers should agree within sampling error; any gap is a modelling bug
(r212 side effects the DP ignores: the monk on 8, the priestess on 10, the
defiled temple on 2).
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot
from camp_dp import camp_action, camp_value

TEMPLE = '0611'


def sim(days, gold, trials=2000, seed0=0):
    wins = 0
    side = {}
    for t in range(trials):
        g = Game(seed=seed0 + t * 7919)
        g.hex = TEMPLE
        g.gold = gold
        g.day = 70 - days + 1
        g.party = [c for c in g.party if 'Prince' in c.name]
        b = Bot(g, 'balanced')
        def chooser(p):
            idx = b.choose(p)
            title = p.get('title', '').lower()
            if 'offerings' in title:
                want = camp_action(max(1, 70 - g.day + 1), g.gold,
                                   g.offering_bonus, g.omen_bonus,
                                   g.influence_bonus, g.wit >= 5)
                for i, o in enumerate(p['options']):
                    lab = o['label'].lower()
                    if (isinstance(want, int) and lab.startswith('offer')) or \
                            (want == 'news' and 'news' in lab) or \
                            (want == 'rest' and 'withdraw' in lab):
                        idx = i
                        break
            return idx
        g.run_until_idle(max_steps=4000, chooser=chooser)
        wins += 1 if g.staff else 0
        for line in g.log:
            if 'Offering of' in line:
                total = int(line.split('=')[1].split('(')[0].strip())
                side[total] = side.get(total, 0) + 1
    return wins / trials, side


if __name__ == '__main__':
    for days, gold in [(20, 100), (20, 200), (15, 100), (10, 100), (25, 150),
                       (30, 60), (12, 60), (8, 60), (20, 500), (40, 120)]:
        got, side = sim(days, gold, 1500)
        want = camp_value(days, gold, 0, 0, 0, False)
        print(f'days {days:2} gold {gold:3}: DP {want:.4f}  engine {got:.4f}  '
              f'diff {got - want:+.4f}')
        if days == 20 and gold == 100:
            print('   offering totals:', dict(sorted(side.items())))
