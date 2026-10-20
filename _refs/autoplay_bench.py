"""Compare auto-play personalities across several seeds.

    python _refs/autoplay_bench.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import run, STRATEGIES

SEEDS = (1, 7, 42, 123, 999, 2026)


def main():
    for seed in SEEDS:
        for strat in STRATEGIES:
            g = Game(seed=seed)
            steps = run(g, strat, 6000)
            s = g.status()
            print(f'{seed:>5} {strat:<11} steps {steps:>4}  day {s["day"]:>2}  '
                  f'hex {s["hex"]}  gold {s["gold"]:>4}  food {s["food"]:>3}  '
                  f'party {len(s["party"])}  staff {s["staff"]}  '
                  f'visited {len(g.visited):>3}  | {s["reason"][:46]}')
        print()


if __name__ == '__main__':
    main()
