import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
b = Bot(g, 'balanced')
g.run_until_idle(6000, b.choose)
print('log lines:', len(g.log))
for line in g.log[:70]:
    print(line)
