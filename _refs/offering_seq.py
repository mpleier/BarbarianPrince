"""Print the offering sequence for every game: what was offered, the roll,
and what the High Priest did afterwards."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
OFF = re.compile(r'Offering of (\d+) gold: dice (\d+) \+ (\d+) = (\d+)')

wins = 0
influence_taken = 0
influence_used = 0
for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    seq = []
    infl = 0
    for line in g.log:
        m = OFF.search(line)
        if m:
            seq.append(tuple(int(x) for x in m.groups()))
        if 'Influence accepted' in line:
            infl += 1
    influence_taken += infl
    for amount, dice, bonus, total in seq:
        if bonus >= 4:
            influence_used += 1
    if g.won:
        wins += 1
        print(f'seed {seed}: WON on offering {seq[-1]} after {len(seq)} offerings')
    elif infl:
        print(f'seed {seed}: {infl} influence(s) but {len(seq)} offerings, '
              f'last={seq[-1]}, gold={g.gold}')
print(f'wins {wins}/{N}, influence taken {influence_taken}, '
      f'offerings with bonus>=4 {influence_used}')
