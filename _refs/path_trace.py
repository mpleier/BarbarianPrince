import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
while not g.game_over:
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    idx = bot.choose(p)
    if p['kind'] == 'choice' and 'action in hex' in p['title'].lower():
        goal = bot.goal_hex()
        print(f'day {g.day:>3} hex {g.hex} gold {g.gold:>4} goal {goal} '
              f'-> {p["options"][idx]["label"][:26]}')
    g.answer(idx)
print('visited:', sorted(g.visited))
print('temples visited:', [h for h in g.visited if g.place_kind(h) == 'temple'])