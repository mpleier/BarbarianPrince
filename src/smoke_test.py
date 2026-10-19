"""Quick headless smoke test of the rules engine."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from engine import Game



def auto_play(seed, days=12, verbose=True):
    g = Game(seed=seed)
    g.run_until_idle(max_steps=days * 40)
    if verbose:
        s = g.status()
        print(f"day {s['day']:>2} hex {s['hex']} gold {s['gold']} "
              f"food {s['food']} party {len(s['party'])}")
    return g



if __name__ == '__main__':
    for seed in (1, 7, 42, 123):
        print('=' * 60, 'seed', seed)
        g = auto_play(seed, days=10, verbose=False)
        for line in g.log:
            print('  ', line)
        print('  FINAL:', g.status())
