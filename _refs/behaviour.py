"""Per-game behaviour report: where the days go and what the bot achieves."""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
OFF = re.compile(r'Offering of (\d+) gold: dice (\d+) \+ (\d+) = (\d+)')
NEWS = re.compile(r'Seeking news: rolled (\d+)')

for strategy in ('balanced', 'aggressive', 'cautious'):
    wins = 0
    reach_temple = 0
    offerings = Counter()
    news_rolls = 0
    omen = 0
    influence = 0
    ruin_days = 0
    travel_days = 0
    first_temple = []
    for seed in range(1, N + 1):
        g = Game(seed=seed)
        bot = Bot(g, strategy)
        g.run_until_idle(max_steps=6000, chooser=bot.choose)
        if g.won:
            wins += 1
        if g.offering_bonus:
            omen += 1
        n_off = 0
        n_infl = 0
        for line in g.log:
            m = OFF.search(line)
            if m:
                n_off += 1
                offerings[int(m.group(4))] += 1
            if NEWS.search(line):
                news_rolls += 1
            if 'influence' in line.lower() and 'three' in line.lower():
                n_infl += 1
            if 'Searching the ruins' in line:
                ruin_days += 1
        offerings_total = n_off
        influence += n_infl
        visited_temples = [h for h in g.visited if g.place_kind(h) == 'temple']
        if visited_temples:
            reach_temple += 1
            idx = [i for i, line in enumerate(g.log) if 'Offerings at' in line]
            if idx:
                first_temple.append(idx[0])
        travel_days += sum(1 for line in g.log if 'Travel to' in line)
    print(f'{strategy:11} wins {wins}/{N}  reached temple {reach_temple}/{N}  '
          f'offerings {offerings_total}  news {news_rolls}  omen {omen}  '
          f'influence {influence}  ruin searches {ruin_days}')
    print('    offering totals:', dict(sorted(offerings.items())))
    print('    avg days to first offering: %.1f'
          % (sum(first_temple) / max(1, len(first_temple))))
