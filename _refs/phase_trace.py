"""Print every day of a campaign: where the bot is, what it is doing, and its goal."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot

seeds = [int(s) for s in sys.argv[1:]] or [1]
for seed in seeds:
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    orig = g.daily_menu

    def wrapped():
        print('day %3d %s %-10s gold %4d ruins %2d cap %3d goal %s mining %s'
              % (g.day, g.hex, g.place_kind(g.hex), g.gold,
                 b.ruin_days, b.ruins_cap(), b.goal_hex(), b.mining()))
        return orig()

    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    print('WIN' if g.staff else 'LOSS', g.reason[:90])
    print()
