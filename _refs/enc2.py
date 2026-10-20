import sys
sys.path.insert(0, 'src')
from engine import Game, parse_foes
from autoplay import Bot

g = Game(seed=1)
bot = Bot(g, 'balanced')
steps = 0
while steps < 6000 and not g.game_over:
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    if p['kind'] == 'encounter':
        print('===', p['title'])
        print(p['text'][:300])
        for i, o in enumerate(p['options']):
            print('   ', i, o['label'])
        print('   -> bot chose', bot.choose(p))
        print()
    idx = bot.choose(p)
    g.answer(idx)
    steps += 1
