"""Where does the bot's gold actually come from, and where does it go?

Aggregates every log line that changes gold over a batch of campaigns.
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40

GAIN = re.compile(r'(?:gain|find|loot|pay|yield|receive)\s+(\d+)', re.I)
SPEND = re.compile(r'(?:pay|spend|cost|bought|wages|lodging)\s+(\d+)', re.I)

gains = Counter()
spends = Counter()
totals = []
for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    totals.append((g.gold, g.peak_gold, g.day))
    for line in g.log:
        m = GAIN.search(line)
        if m:
            gains[line.split(':')[0].split(' - ')[0]] += int(m.group(1))
        m = SPEND.search(line)
        if m:
            spends[line.split(':')[0].split(' - ')[0]] += int(m.group(1))

print('total gold gained: %d' % sum(gains.values()))
for k, v in gains.most_common(15):
    print('  %-40s %d' % (k[:40], v))
print('total gold spent: %d' % sum(spends.values()))
for k, v in spends.most_common(15):
    print('  %-40s %d' % (k[:40], v))
print('avg final gold %.1f, avg peak %.1f'
      % (sum(t[0] for t in totals) / N, sum(t[1] for t in totals) / N))
