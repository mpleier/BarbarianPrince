import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot

orig_finish = Game.finish_day

def finish_day(self):
    print(f'end day {self.day:>2} hex {self.hex} kind {str(self.place_kind(self.hex)):<7} '
          f'gold {self.gold:>4} action {self.action}')
    return orig_finish(self)

Game.finish_day = finish_day

g = Game(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 4)
b = Bot(g, 'balanced')
g.run_until_idle(max_steps=6000, chooser=b.choose)
print('final gold', g.gold, 'staff', g.staff, 'day', g.day, 'peak', g.peak_gold)
