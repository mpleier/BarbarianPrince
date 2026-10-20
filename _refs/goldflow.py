import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
prev_gold = 0
g.run_until_idle(max_steps=6000, chooser=bot.choose)
for line in g.log:
    low = line.lower()
    if 'loot' in low or 'gain' in low or 'offer' in low or 'treasure' in low \
            or 'news roll' in low or 'ruins' in low:
        print(line)
print('final gold', g.gold, 'day', g.day, 'party', len(g.living()))
