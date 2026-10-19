"""Terminal interface for the Barbarian Prince engine.

Useful for quick play-throughs and for testing the engine without Tk.
"""
import sys

from engine import Game


def render(prompt):
    print('\n' + '=' * 60)
    print(prompt['title'])
    if prompt['text']:
        print(prompt['text'])
    for i, opt in enumerate(prompt['options']):
        print(f'  {i + 1}. {opt["label"]}')
    while True:
        try:
            raw = input('Choose: ').strip()
        except EOFError:
            return 0
        if raw.isdigit() and 1 <= int(raw) <= len(prompt['options']):
            return int(raw) - 1
        print('Invalid choice.')


def play_cli(seed=None):
    game = Game(seed=seed)
    index = 0
    while not game.game_over:
        game.advance()
        while game.prompts and not game.game_over:
            for line in game.log[index:]:
                print('  ' + line)
            index = len(game.log)
            p = game.current()
            if p['kind'] == 'info' or not p['options']:
                print('>> ' + p['title'] + ': ' + p['text'])
                game.answer(0)
                continue
            choice = render(p)
            game.answer(choice)
        for line in game.log[index:]:
            print('  ' + line)
        index = len(game.log)
        s = game.status()
        print(f"[day {s['day']} hex {s['hex']} gold {s['gold']} food {s['food']} "
              f"wit {s['wit']} party {len(s['party'])}]")
    print('\n*** ' + (game.reason or 'Game over'))


if __name__ == '__main__':
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    play_cli(seed)
