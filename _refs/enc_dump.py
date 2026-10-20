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
    if p['kind'] == 'encounter':
        opts = [o['label'] for o in p['options']]
        print(f'ENC {p["title"][:40]} -> chose {opts[idx][:30]} '
              f'(of {len(opts)}) | gold {g.gold} party {len(g.living())}')
    g.answer(idx)
    steps += 1
print('final gold', g.gold, 'day', g.day)
