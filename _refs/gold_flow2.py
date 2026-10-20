"""Track gold flow: income vs. expenditure, and the time spent in each place."""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40

GAIN = re.compile(r'(?:gain|find|receive)\s+(\d+)\s*gold', re.I)
SPEND = re.compile(r'(?:pay|spend|cost|offering of)\s+(\d+)', re.I)

max_gold = 0
income = 0
spending = 0
days_by_place = Counter()
days_by_action = Counter()
offer_days = 0
ruin_days = 0
travel_days = 0
news_days = 0
for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    max_gold = max(max_gold, g.peak_gold)
    prev = 0
    for line in g.log:
        m = GAIN.search(line)
        if m:
            income += int(m.group(1))
        m = SPEND.search(line)
        if m:
            spending += int(m.group(1))
    kind = None
    for line in g.log:
        if 'Searching the ruins' in line:
            ruin_days += 1
        if 'Offering of' in line:
            offer_days += 1
        if 'Seeking news' in line:
            news_days += 1
        if 'Travel to' in line:
            travel_days += 1
    days_by_place[g.place_kind(g.hex)] += 1
print(f'games {N}  total income {income}  total spending {spending}  '
      f'peak gold {max_gold}')
print(f'ruin searches {ruin_days}  offerings {offer_days}  '
      f'news {news_days}  travel {travel_days}')
print(f'per game: income {income/N:.1f}  offerings {offer_days/N:.2f}  '
      f'ruin searches {ruin_days/N:.1f}')
