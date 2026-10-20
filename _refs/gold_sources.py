import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

src = {}
for seed in range(1, 31):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    for line in g.log:
        low = line.lower()
        if 'loot from' in low:
            src['combat loot'] = src.get('combat loot', 0) + 1
        elif 'gain 50 gold' in low or 'gain ' in low and 'gold from' in low:
            src['event gold'] = src.get('event gold', 0) + 1
        elif 'thieves' in low:
            src['news den'] = src.get('news den', 0) + 1
        elif 'offerings' in low and 'rolled' in low:
            src['offerings'] = src.get('offerings', 0) + 1
        elif 'no gold to offer' in low:
            src['failed offerings'] = src.get('failed offerings', 0) + 1
        elif 'combat:' in low:
            src['combats'] = src.get('combats', 0) + 1
        elif 'combat ends' in low:
            src['combat ends'] = src.get('combat ends', 0) + 1
        elif 'ruin' in low and 'search' in low:
            src['ruins searches'] = src.get('ruins searches', 0) + 1
print(src)