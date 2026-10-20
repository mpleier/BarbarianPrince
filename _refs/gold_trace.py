import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

for seed in (1, 2, 3, 42):
    g = Game(seed=seed)
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    print(f'=== seed {seed}: day {g.day} gold {g.gold} party {len(g.living())} '
          f'won {g.won} reason {g.reason}')
    for line in g.log:
        low = line.lower()
        if any(k in low for k in ('gold', 'loot', 'treasure', 'offering', 'temple')):
            print('   ', line)
    print()
