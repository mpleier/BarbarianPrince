"""Per-day gold accounting: how much does each phase actually net?"""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 150

ruin_day_net = []
temple_day_net = []
travel_day_net = []
other_day_net = []
offer_amounts = []
offer_totals = []

for seed in range(1, N + 1):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    last_day = g.day
    last_gold = g.gold
    last_kind = None
    last_label = ''

    def wrapped(prompt):
        i = bot.choose(prompt)
        title = prompt.get('title', '')
        label = prompt['options'][i]['label']
        if 'Submit offerings' in title:
            offer_amounts.append(label)
            if label.startswith('Offer'):
                offer_totals.append(int(label.split()[1]))
        if 'action in hex' in title.lower():
            kind = g.place_kind(g.hex) or 'open'
            last_kind = kind
            last_label = label
        return i

    g.run_until_idle(max_steps=6000, chooser=wrapped)

    # reconstruct daily nets from the log
    day_gold = {}
    for line in g.log:
        pass

print('offer labels seen:')
from collections import Counter
for k, v in Counter(offer_amounts).most_common(10):
    print(' ', v, k)
print('avg offering size:', sum(offer_totals) / max(1, len(offer_totals)))
print('total offerings:', len(offer_totals) / N, 'per game')
