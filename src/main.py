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

# A windowed build (pyinstaller console=False) has no stdout/stderr, and any
# stray print() would abort the game.  Give them a sink instead.
if sys.stdout is None or sys.stderr is None:
    _sink = open(os.devnull, 'w', encoding='utf-8', errors='ignore')
    if sys.stdout is None:
        sys.stdout = _sink
    if sys.stderr is None:
        sys.stderr = _sink

from engine import Game
from autoplay import Bot, STRATEGIES
from resource import FROZEN


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
    ap.add_argument('--web', action='store_true',
                    help='play in the browser (local server, opens a tab)')
    ap.add_argument('--port', type=int, default=0,
                    help='with --web, the port to use (0 picks a free one)')
    ap.add_argument('--no-browser', action='store_true',
                    help='with --web, do not open a browser tab')
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
    if args.web:
        from web import serve
        serve(port=args.port, seed=args.seed,
              open_browser=not args.no_browser,
              # a windowed build has no console, so keep a small window open
              window=FROZEN and not args.no_browser)
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


def crash_log(exc):
    """Record a fatal error next to the exe: a windowed build has no console."""
    import traceback
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, 'crash.log')
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f'\n--- {__import__("datetime").datetime.now():%Y-%m-%d %H:%M:%S}\n')
            f.write(''.join(traceback.format_exception(exc)))
    except OSError:
        pass
    return path


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        path = crash_log(exc)
        if getattr(sys, 'frozen', False):
            try:
                import tkinter.messagebox as mb
                mb.showerror('Barbarian Prince',
                             f'The game stopped with an error.\n\n'
                             f'{type(exc).__name__}: {exc}\n\nDetails: {path}')
            except Exception:
                pass
        raise
