"""Print the phase sequence of a campaign so temple/ruin ping-pong is visible."""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot


def trace(seed, limit=70):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    orig = g.daily_menu
    seq = []

    def menu():
        kind = g.place_kind(g.hex) or 'open'
        if not seq or seq[-1][1] != kind:
            seq.append((g.day, kind, g.gold))
        return orig()

    g.daily_menu = menu
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    print(f'seed {seed}: win={bool(g.staff)}')
    for day, kind, gold in seq:
        print(f'  day {day:3} {kind:8} gold {gold:5}')


if __name__ == '__main__':
    for s in [int(x) for x in sys.argv[1:]] or [2, 4, 6]:
        trace(s)
