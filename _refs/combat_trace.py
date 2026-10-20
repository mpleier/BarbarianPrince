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

out = []
for line in g.log:
    low = line.lower()
    if any(k in low for k in ('combat', 'loot', 'gold', 'battle', 'round', 'wound', 'kill', 'rout', 'hire', 'flee', 'escape')):
        out.append(line)
print('\n'.join(out))
print('FINAL gold', g.gold, 'day', g.day, 'party', len(g.living()))
