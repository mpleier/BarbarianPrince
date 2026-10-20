"""Full gold-flow audit: every prompt, its gold delta, grouped by prompt title.

Also reports the per-day drain from food (r215) and lodging (r217).
"""
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

BY_TITLE = defaultdict(lambda: [0, 0])
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40

for s in range(1, N + 1):
    g = Game(seed=s)
    bot = Bot(g, 'balanced')
    steps = 0
    while steps < 6000 and not g.game_over:
        g.advance()
        if not g.prompts or g.game_over:
            break
        prompt = g.current()
        title = prompt.get('title', '')
        idx = bot.choose(prompt)
        before = g.gold
        g.answer(idx)
        BY_TITLE[title][0] += 1
        BY_TITLE[title][1] += g.gold - before
        steps += 1

rows = sorted(BY_TITLE.items(), key=lambda x: x[1][1])
for title, (c, gold) in rows:
    if gold or c > 50:
        print(f'{title[:44]:44} n={c:6} gold={gold:8} avg={gold / max(1, c):7.2f}')
