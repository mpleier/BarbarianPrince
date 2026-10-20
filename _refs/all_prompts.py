import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
steps = 0
kinds = {}
while steps < 6000 and not g.game_over:
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    kinds[p['kind']] = kinds.get(p['kind'], 0) + 1
    if p['kind'] in ('encounter', 'combat'):
        print(f"[{p['kind']}] {p['title']} | gold {g.gold} party {len(g.living())}")
        for i, o in enumerate(p['options']):
            print('    ', i, o['label'])
        print('    -> chose', bot.choose(p))
    idx = bot.choose(p)
    g.answer(idx)
    steps += 1
print('prompt kinds:', kinds)
print('final gold', g.gold, 'day', g.day, 'party', len(g.living()))
