import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
steps = 0
while steps < 6000 and not g.game_over:
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    idx = bot.choose(p)
    g.answer(idx)
    steps += 1
    if p['kind'] == 'choice' and 'action in hex' in p['title'].lower():
        print(f"day {g.day:>3} hex {g.hex} gold {g.gold:>4} party {len(g.living())} -> {p['options'][idx]['label']}")
print('final', g.gold, g.day, g.won, g.reason)
