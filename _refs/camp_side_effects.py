"""What actually happens on a camp day.

The camp DP assumes a temple day is exactly "pay the offering, roll 2d6,
nothing else happens".  The engine has extra branches (r212 result 8 hands
you a monk, result 10 makes you flee the temple with a priestess, result 2
defiles the temple).  This audit measures how often those branches fire and
what they cost.
"""
import sys
sys.path.insert(0, 'src')

from collections import Counter

from engine import Game
from autoplay import Bot


def run(seed, strategy='balanced'):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    events = Counter()
    gold_lost = 0
    party_days = 0
    left_temple = 0
    prev = None

    def chooser(prompt):
        nonlocal gold_lost, party_days, left_temple, prev
        idx = b.choose(prompt)
        title = prompt.get('title', '').lower()
        if 'action in hex' in title and g.place_kind(g.hex) == 'temple':
            before = g.gold
            prev = (g.day, g.hex, g.gold, len(g.living()))
        return idx

    def post(prompt):
        pass

    g.run_until_idle(max_steps=6000, chooser=chooser)
    return events, gold_lost, party_days, left_temple


def main(n, strategy='balanced'):
    tally = Counter()
    for s in range(1, n + 1):
        g = Game(seed=s)
        b = Bot(g, strategy)
        camp_days = 0
        party_days = 0
        fled = 0
        def chooser(prompt):
            nonlocal camp_days, party_days, fled
            idx = b.choose(prompt)
            title = prompt.get('title', '').lower()
            if 'action in hex' in title and g.place_kind(g.hex) == 'temple':
                camp_days += 1
                party_days += len(g.living())
            return idx
        g.run_until_idle(max_steps=6000, chooser=chooser)
        for line in g.log:
            if 'Offering of' in line:
                tally['offer'] += 1
            if 'monk' in line.lower():
                tally['monk'] += 1
            if 'priestess' in line.lower():
                tally['priestess'] += 1
            if 'impure' in line.lower():
                tally['defiled'] += 1
            if 'influence' in line.lower():
                tally['influence'] += 1
        tally['camp_days'] += camp_days
        tally['party_days'] += party_days
        tally['wins'] += 1 if g.staff else 0
    print(dict(tally))
    print('avg camp days', tally['camp_days'] / n)
    print('avg party days at temple', tally['party_days'] / n)
    print('win rate', tally['wins'] / n)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300,
         sys.argv[2] if len(sys.argv) > 2 else 'balanced')
