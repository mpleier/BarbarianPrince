"""Dump the distinct action labels the bot actually takes, and ruin gold deltas."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot
from collections import Counter

labels = Counter()
deltas = []
for seed in range(1, 40):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    steps = 0
    while not g.game_over and steps < 6000:
        p = g.current()
        if not p:
            break
        i = bot.choose(p)
        opts = p.get('options') or []
        if not opts:
            break
        label = opts[i].get('label', '')
        labels[label] += 1
        before = g.gold
        g.answer(i)
        if 'r208' in label:
            deltas.append(g.gold - before)
        steps += 1

deltas.sort()
n = len(deltas)
with open('_refs/ruin_yield_out.txt', 'w', encoding='utf-8') as fh:
    fh.write(f'ruin searches {n}\n')
    if n:
        fh.write(f'mean {sum(deltas)/n:.2f} median {deltas[n//2]} '
                 f'p25 {deltas[n//4]} p75 {deltas[3*n//4]} min {deltas[0]} max {deltas[-1]}\n')
        fh.write(f'non-positive: {sum(1 for x in deltas if x <= 0)}/{n}\n')
    for k, v in labels.most_common(30):
        fh.write(f'{v:>4} | {k}\n')
print('done', n)
