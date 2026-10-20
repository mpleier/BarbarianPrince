"""Sweep the ruin-farming cap to find the optimal macro split.

The bot's ruins_cap() decides how long it stays at a ruin before heading to a
temple.  Too high -> it arrives at the temple with almost no days left.
Too low -> it arrives at the temple broke.

This sweeps the cap and reports the resulting win rate.
"""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300

def run(cap, strategy='balanced'):
    wins = 0
    temple_days = []
    gold_arrive = []
    reached = 0
    for seed in range(1, N + 1):
        g = Game(seed=seed)
        bot = Bot(g, strategy)
        if cap is not None:
            bot.ruins_cap = lambda cap=cap: cap
        g.run_until_idle(max_steps=6000, chooser=bot.choose)
        if g.staff:
            wins += 1
    return wins / N

print(f'{"cap":>6}  win rate')
for cap in (10, 20, 30, 40, 50, 60, 80, 100, 150, 200, 300, 500):
    print(f'{cap:>6}  {run(cap)*100:.2f}%')
print()
print('default (dynamic cap):', f'{run(None)*100:.2f}%')
