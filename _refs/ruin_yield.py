"""Measure the true per-action gold yield of ruin searching."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

deltas = []
for seed in range(1, 61):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    steps = 0
    while not g.game_over and steps < 6000:
        p = g.current()
        if not p:
            break
        i = bot.choose(p)
        label = p['options'][i]['label']
        before = g.gold
        g.answer(i)
        if 'r208' in label:
            deltas.append(g.gold - before)
        steps += 1

deltas.sort()
n = len(deltas)
print(f'ruin searches: {n}, mean {sum(deltas)/n:.2f}, median {deltas[n//2]}, '
      f'p25 {deltas[n//4]}, p75 {deltas[3*n//4]}, min {deltas[0]}, max {deltas[-1]}')
print('zero-or-negative:', sum(1 for x in deltas if x <= 0), '/', n)
