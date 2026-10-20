import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

for seed in range(1, 11):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    actions = []
    golds = []
    while not g.game_over:
        g.advance()
        if not g.prompts or g.game_over:
            break
        p = g.current()
        idx = bot.choose(p)
        label = p['options'][idx]['label']
        if p['kind'] == 'choice' and 'action in hex' in p['title'].lower():
            actions.append((g.day, g.hex, g.gold, label[:22]))
        g.answer(idx)
        golds.append(g.gold)
    print(f'seed {seed}: day {g.day} gold {g.gold} won {g.won} '
          f'temples {len([h for h in g.visited if g.place_kind(h) == "temple"])}')
    print('   peak gold', max(golds), 'actions:', actions[:25])