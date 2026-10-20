import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

for strategy in ('balanced', 'aggressive'):
    totals = {'loot': 0, 'news': 0, 'ruins': 0, 'other': 0}
    max_gold = 0
    for seed in range(1, 21):
        g = Game(seed=seed)
        bot = Bot(g, strategy)
        g.run_until_idle(6000, bot.choose)
        max_gold = max(max_gold, g.gold)
        for line in g.log:
            low = line.lower()
            if 'loot from' in low:
                totals['loot'] += 1
            elif 'gain 50 gold' in low or 'gain' in low and 'gold from' in low:
                totals['news'] += 1
    print(strategy, 'max gold seen:', max_gold, totals)
