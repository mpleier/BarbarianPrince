"""Where do the 70 days actually go, and how much gold is converted into
offerings?  Reports per-strategy aggregates over N seeds."""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100

OFF = re.compile(r'Offering of (\d+) gold')
DAY = re.compile(r'^Day (\d+)')

for strategy in ('cautious', 'balanced', 'aggressive'):
    wins = 0
    totals = Counter()
    offer_amounts = Counter()
    for seed in range(1, N + 1):
        g = Game(seed=seed)
        bot = Bot(g, strategy)
        g.run_until_idle(max_steps=6000, chooser=bot.choose)
        wins += 1 if g.staff else 0
        temple_days = 0
        ruin_days = 0
        cur_hex = None
        for line in g.log:
            m = DAY.match(line)
            if m:
                pass
            if 'begins in hex' in line:
                cur_hex = line.split('hex ')[1].strip('.')
                kind = g.place_kind(cur_hex)
                if kind == 'temple':
                    temple_days += 1
                elif kind == 'ruins':
                    ruin_days += 1
            m = OFF.search(line)
            if m:
                offer_amounts[int(m.group(1))] += 1
        totals['temple_days'] += temple_days
        totals['ruin_days'] += ruin_days
        totals['gold_end'] += g.gold
        totals['news'] += sum(1 for l in g.log if 'Seeking news' in l)
        totals['omen'] += 1 if g.offering_bonus else 0
        totals['influence'] += sum(1 for l in g.log if 'influence' in l.lower())
        totals['no_gold'] += sum(1 for l in g.log if 'no gold' in l.lower())
    print(f'{strategy:<10} wins {wins:>3}/{N}  temple_days {totals["temple_days"]/N:6.1f}  '
          f'ruin_days {totals["ruin_days"]/N:5.1f}  news {totals["news"]/N:5.1f}  '
          f'omen {totals["omen"]/N:4.2f}  influence {totals["influence"]/N:5.1f}  '
          f'no-gold {totals["no_gold"]/N:5.1f}  end gold {totals["gold_end"]/N:6.1f}')
    print('   offering amounts:', dict(offer_amounts))
