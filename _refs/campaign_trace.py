"""Print every prompt of one campaign so the day-by-day flow is visible."""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot


def trace(seed, strategy='balanced'):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    out = []

    def chooser(prompt):
        idx = b.choose(prompt)
        title = prompt.get('title', '')
        label = (prompt.get('options') or [{}])[idx].get('label', '')
        out.append(f'{g.day:3} {g.hex} {g.place_kind(g.hex) or "open":8} '
                  f'gold {g.gold:5} | {title[:40]:40} -> {label[:40]}')
        return idx

    g.run_until_idle(max_steps=6000, chooser=chooser)
    out.append(f'END day {g.day} gold {g.gold} staff {bool(g.staff)} {g.reason}')
    print('\n'.join(out))


if __name__ == '__main__':
    trace(int(sys.argv[1]) if len(sys.argv) > 1 else 2,
          sys.argv[2] if len(sys.argv) > 2 else 'balanced')
