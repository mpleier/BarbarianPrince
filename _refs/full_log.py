import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

g = Game(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 1)
bot = Bot(g, 'balanced')
g.run_until_idle(max_steps=6000, chooser=bot.choose)
for line in g.log:
    print(line)
