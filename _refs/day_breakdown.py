"""Per-game breakdown of the bot's day-by-day behaviour.

Reports, for each strategy over a batch of seeds:
  * how many days the party spent in ruins vs at a temple
  * how many offerings were made and with what modifiers
  * how often the permanent news omen (r209 result 4) ever lands
  * the win rate
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40

for strategy in ('balanced', 'aggressive', 'cautious'):
    wins = 0
    ruin_days = 0
    temple_days = 0
    travel_days = 0
    other_days = 0
    offerings = 0
    omen_games = 0
    influence_games = 0
    first_temple_day = []
    gold_at_first_temple = []
    for seed in range(1, N + 1):
        g = Game(seed=seed)
        bot = Bot(g, strategy)
        g.run_until_idle(max_steps=6000, chooser=bot.choose)
        if g.won:
            wins += 1
        if g.offering_bonus:
            omen_games += 1
        kinds = Counter()
        for line in g.log:
            low = line.lower()
            if 'searching the ruins' in low:
                kinds['ruin'] += 1
            if 'offering of' in low:
                kinds['offer'] += 1
            if 'seeking news' in low:
                kinds['news'] += 1
            if 'influence' in low and 'add three' in low:
                kinds['influence'] += 1
        ruin_days += kinds['ruin']
        offerings += kinds['offer']
        influence_games += 1 if kinds['influence'] else 0
        temple_days += sum(1 for h in g.visited if g.place_kind(h) == 'temple')
        first = next((i for i, h in enumerate(g.visited)
                      if g.place_kind(h) == 'temple'), None)
        if first is not None:
            first_temple_day.append(first)
            gold_at_first_temple.append(g.gold)
    print(f'{strategy:11} wins {wins}/{N}  offerings {offerings}  '
          f'ruin searches {ruin_days}  news {0}')
    print(f'    omen earned in {omen_games}/{N} games, '
          f'influence used in {influence_games}/{N}')
    print(f'    temple visits {temple_days}, '
          f'first temple on step {sum(first_temple_day)/max(1,len(first_temple_day)):.0f}')
