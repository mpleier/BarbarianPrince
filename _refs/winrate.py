"""Win-rate harness: run N seeds for each strategy and report the win rate."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot, STRATEGIES

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
strategies = sys.argv[2:] or list(STRATEGIES)

for strategy in strategies:
    wins = 0
    days = []
    staff = 0
    gold = []
    for seed in range(1, N + 1):
        g = Game(seed=seed)
        bot = Bot(g, strategy)
        try:
            g.run_until_idle(max_steps=6000, chooser=bot.choose)
        except Exception as exc:
            print(f'seed {seed} crashed: {exc}')
            continue
        if g.staff:
            wins += 1
        if g.staff or g.game_over:
            staff += 1
        days.append(g.day)
        gold.append(g.gold)
    print(f'{strategy:<10} wins {wins:>4}/{N}  rate {wins / N:.3f}  '
          f'avg days {sum(days) / len(days):.1f}  avg gold {sum(gold) / len(gold):.1f}')
