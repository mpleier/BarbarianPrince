import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
steps = 0
seen = set()
while steps < 6000 and not g.game_over:
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    if p['kind'] == 'action':
        print(f'ACTION day {g.day} hex {g.hex} gold {g.gold} party {len(g.living())}')
        for o in p['options']:
            print('   ', o['label'])
        seen.add(tuple(sorted(o['label'] for o in p['options'])))
    idx = bot.choose(p)
    g.answer(idx)
    steps += 1
print('distinct action menus:', len(seen))
for s in list(seen)[:6]:
    print(s)
