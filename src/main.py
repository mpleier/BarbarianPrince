"""Entry point: run the Barbarian Prince game.

    python src/main.py              # graphical (Tk) game
    python src/main.py --cli        # terminal game
    python src/main.py --seed 42    # reproducible game
    python src/main.py --auto       # let the engine play itself (smoke test)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import Game


def auto(seed):
    game = Game(seed=seed)
    game.run_until_idle(max_steps=4000)
    status = game.status()
    print('day', status['day'], 'hex', status['hex'], 'gold', status['gold'],
          'food', status['food'], 'party', status['party'])
    print('result:', status['reason'])
    for line in game.log[-40:]:
        print('  ', line)


def main():
    ap = argparse.ArgumentParser(description='Barbarian Prince game engine')
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--cli', action='store_true', help='play in the terminal')
    ap.add_argument('--auto', action='store_true', help='auto-play (no input)')
    args = ap.parse_args()

    if args.auto:
        auto(args.seed)
        return
    if args.cli:
        from cli import play_cli
        play_cli(args.seed)
        return
    try:
        from gui import GameGUI
    except Exception as exc:  # Tk unavailable
        print('GUI unavailable (%s) - falling back to the terminal.' % exc)
        from cli import play_cli
        play_cli(args.seed)
        return
    GameGUI(Game(seed=args.seed)).run()


if __name__ == '__main__':
    main()
