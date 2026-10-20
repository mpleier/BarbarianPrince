import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
steps = 0
prev = 0
while steps < 6000 and not g.game_over:
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    idx = bot.choose(p)
    g.answer(idx)
    steps += 1
    if g.gold != prev:
        print(f'gold {prev} -> {g.gold} day {g.day} hex {g.hex} | {p["title"][:45]} | {p["options"][idx]["label"][:30]}')
        prev = g.gold
print('final gold', g.gold, 'day', g.day, 'won', g.won)
print('--- log lines mentioning gold ---')
for line in g.log:
    if 'gold' in line.lower() or 'loot' in line.lower() or 'treasure' in line.lower():
        print(' ', line)
