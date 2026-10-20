"""Find campaigns that never reach a temple and trace why."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
zero = []
for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    offers = sum(1 for l in g.log if 'Offering of' in l)
    if offers == 0:
        zero.append((seed, g.hex, g.gold, g.day,
                     sum(1 for l in g.log if 'Searching the ruins' in l)))
print(f'{len(zero)} of {N} games never offered at a temple')
for seed, hex_, gold, day, ru in zero[:12]:
    print(f'  seed {seed}: end hex {hex_} gold {gold} day {day} ruin days {ru}')
