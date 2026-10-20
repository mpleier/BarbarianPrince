"""Per-game macro audit: how the 70 days are actually spent."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

rows = []
for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    marks = []
    orig = g.daily_menu

    def wrapped():
        marks.append((g.day, g.hex, g.place_kind(g.hex), g.gold, len(g.log)))
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    ruin = travel = temple = news = 0
    at_ruin = at_temple = 0
    first_temple_day = None
    for i in range(len(marks) - 1):
        day, hex_, kind, gold, li = marks[i]
        window = g.log[li:marks[i + 1][4]]
        if kind == 'ruins':
            at_ruin += 1
        elif kind == 'temple':
            at_temple += 1
        if kind == 'ruins' and any(l.startswith('Searching the ruins') for l in window):
            ruin += 1
        elif any(l.startswith('Offering of') for l in window):
            temple += 1
        elif any(l.startswith('Seeking news') for l in window):
            news += 1
        elif any(l.startswith('Travel action') for l in window):
            travel += 1
        if kind == 'temple' and first_temple_day is None:
            first_temple_day = day
    rows.append((ruin, travel, temple, news, g.gold, g.staff,
                 first_temple_day or 0, at_ruin, at_temple))

def avg(i):
    return sum(r[i] for r in rows) / len(rows)

wins = sum(1 for r in rows if r[5])
print(f'{N} games {strategy}: win {wins / N:.3f}')
print(f'avg ruin days {avg(0):.1f}  travel days {avg(1):.1f}  temple days {avg(2):.1f}  news days {avg(3):.1f}')
print(f'avg final gold {avg(4):.1f}  avg first temple day {avg(6):.1f}')
print(f'avg days standing on a ruins hex {avg(7):.1f}, on a temple hex {avg(8):.1f}')
win_days = [r[2] for r in rows if r[5]]
lose_days = [r[2] for r in rows if not r[5]]
print(f'winners avg temple days {sum(win_days) / max(1, len(win_days)):.1f}, '
      f'losers {sum(lose_days) / max(1, len(lose_days)):.1f}')
print('temple-day histogram:', sorted(Counter(r[2] for r in rows).items()))
