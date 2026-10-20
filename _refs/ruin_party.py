"""Does a party make ruin searching pay better?

r208 adds +1 to the search roll for every follower with combat skill 6+, and
e132 lets an organised party search again the same day.  Both should raise the
yield per day, but followers eat and demand pay.  This measures the raw search
yield for party sizes and skill bonuses, and the net gold per day after the
engine charges for food and lodging.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game, Character


def measure(party_skills, trials=4000, seed=7):
    g = Game(seed=seed)
    g.hex = '0102'
    g.party = [Character('Prince', 8, 9, 0, prince=True)]
    for i, s in enumerate(party_skills):
        g.party.append(Character(f'H{i}', s, 4, 0))
    g.gold = 0
    total = 0
    searches = 0
    for _ in range(trials):
        before = g.gold
        g._ruins_retry = 0
        g.search_ruins()
        while g.prompts:
            g.answer(0)
        total += g.gold - before
        searches += 1
    return total / trials, searches / trials


if __name__ == '__main__':
    for skills in ([], [6], [6, 6], [6, 6, 6], [5], [4, 4], [3, 3, 3, 3]):
        gold, searches = measure(skills)
        n = len(skills) + 1
        print(f'party {n:2} (bonus {sum(s >= 6 for s in skills)})  '
              f'gold/day {gold:7.2f}  searches/day {searches:.2f}')
