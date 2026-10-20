"""How good is the camp strategy on its own?

Start every campaign with a fixed pile of gold so the ruin phase is skipped
entirely; whatever win rate remains is the quality of the temple strategy
alone.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
GOLD = int(sys.argv[2]) if len(sys.argv) > 2 else 200

wins = 0
win_days = []
reasons = {}
for seed in range(1, N + 1):
    g = Game(seed=seed)
    g.gold = GOLD
    b = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    if g.staff:
        wins += 1
        win_days.append(g.day)
    reasons[g.reason] = reasons.get(g.reason, 0) + 1

print(f'{N} campaigns starting with {GOLD} gold: win {wins / N:.3f}')
if win_days:
    print(f'win day: min {min(win_days)}, mean {sum(win_days) / len(win_days):.1f}, '
          f'max {max(win_days)}')
for r, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
    print(f'  {n:>4}  {r}')
