"""Day-by-day trace of one campaign, showing the macro plan in action."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'
g = Game(seed=seed)
b = Bot(g, strategy)
marks = []
orig = g.daily_menu

def wrapped():
    marks.append((g.day, g.hex, g.place_kind(g.hex), g.gold, len(g.log),
                  b.plan(), b.camp_days(), b.ruins_cap(), b.ruin_budget(),
                  b.ruin_days))
    return orig()
g.daily_menu = wrapped
g.run_until_idle(max_steps=6000, chooser=b.choose)

for i in range(len(marks) - 1):
    day, hex_, kind, gold, li, plan, cd, cap, budget, spent = marks[i]
    window = g.log[li:marks[i + 1][4]]
    act = next((l for l in window
                if l.startswith(('Searching', 'Offering', 'Seeking', 'Travel',
                                'The party does nothing'))), 'other')
    print(f'd{day:>3} {hex_} {str(kind):<7} gold {gold:>4}  cap {cap:>4} '
          f'camp {cd:>3} ruin {spent:>2}/{budget:>2} plan {plan}  -> {act[:42]}')
print(f'final: day {g.day} gold {g.gold} staff {g.staff} reason {g.reason}')
