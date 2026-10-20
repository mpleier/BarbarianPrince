"""Record every day of a campaign: where the party is and what it does."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'
show = int(sys.argv[3]) if len(sys.argv) > 3 else 0

tot = Counter()
for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    days = []
    orig = g.daily_menu

    def wrapped():
        days.append((g.day, g.hex, g.place_kind(g.hex), g.gold))
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    for _, _, kind, _ in days:
        tot[kind or 'open'] += 1
    if show and seed == 1:
        for d, h, k, gold in days:
            print(f'{d:>2} {h} {str(k):<8} gold {gold:>4}')
        print('plan', b.plan(), 'ruins_cap', b.ruins_cap())

print('day counts by place kind:', tot.most_common())
print('avg days per game', sum(tot.values()) / N)
