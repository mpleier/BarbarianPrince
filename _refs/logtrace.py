import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
steps = 0
while steps < 400 and not g.game_over:
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    idx = bot.choose(p)
    g.answer(idx)
    steps += 1

for i, line in enumerate(g.log[:160]):
    print(i, line)
print('...')
print('day', g.day, 'gold', g.gold, 'hex', g.hex, 'party', len(g.living()))
