import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
steps = 0
prev_gold = 0
while steps < 6000 and not g.game_over:
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    idx = bot.choose(p)
    g.answer(idx)
    steps += 1
    if g.gold != prev_gold:
        print(f'gold {prev_gold} -> {g.gold} at day {g.day} hex {g.hex} prompt={p["title"][:40]} chose={p["options"][idx]["label"][:30]}')
        prev_gold = g.gold
print('final gold', g.gold, 'day', g.day, 'won', g.won)
print('--- last 25 notes ---')
for n in g.notes[-25:]:
    print(' ', n)
