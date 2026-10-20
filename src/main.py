"""Entry point: run the Barbarian Prince game.

    python src/main.py                                # graphical (Tk) game
    python src/main.py --cli                          # terminal game
    python src/main.py --seed 42                      # reproducible game
    python src/main.py --auto                         # the bot plays a campaign
    python src/main.py --auto --strategy aggressive   # ... aggressively
    python src/main.py --cli --strategy cautious      # bot plays, you watch
    python src/main.py --auto --naive                 # first-option smoke test
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import Game
from autoplay import Bot, STRATEGIES


def auto(seed=None, strategy='balanced', start='0101', naive=False, verbose=False):
    """Run a whole campaign headlessly and report the outcome."""
    game = Game(seed=seed, start_hex=start)
    chooser = None if naive else Bot(game, strategy).choose
    steps = game.run_until_idle(max_steps=6000, chooser=chooser)
    status = game.status()
    print('strategy:', 'naive' if naive else strategy, '| steps:', steps)
    print('day', status['day'], 'hex', status['hex'], 'gold', status['gold'],
          'food', status['food'], 'party', status['party'],
          'staff', status['staff'])
    print('result:', status['reason'])
    for line in (game.log if verbose else game.log[-40:]):
        print('  ', line)


def main():
    ap = argparse.ArgumentParser(description='Barbarian Prince game engine')
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--start', default='0101', help='starting hex id')
    ap.add_argument('--cli', action='store_true', help='play in the terminal')
    ap.add_argument('--auto', action='store_true', help='auto-play (no input)')
    ap.add_argument('--strategy', choices=STRATEGIES, default='balanced',
                    help='bot personality (default: balanced)')
    ap.add_argument('--naive', action='store_true',
                    help='with --auto, answer every prompt with the first option')
    ap.add_argument('--verbose', action='store_true', help='print the whole log')
    args = ap.parse_args()

    if args.auto:
        auto(args.seed, args.strategy, args.start, args.naive, args.verbose)
        return
    if args.cli:
        from cli import play_cli
        play_cli(args.seed, args.strategy, args.start)
        return
    try:
        from gui import GameGUI
    except Exception as exc:  # Tk unavailable
        print('GUI unavailable (%s) - falling back to the terminal.' % exc)
        from cli import play_cli
        play_cli(args.seed, None, args.start)
        return
    GameGUI(Game(seed=args.seed, start_hex=args.start)).run()


if __name__ == '__main__':
    main()
