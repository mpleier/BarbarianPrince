import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

g = Game(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 1)
bot = Bot(g, 'balanced')
day_actions = []

orig_action = Game.begin_action

def begin_action(self, action):
    day_actions.append((self.day, self.hex, action, self.gold))
    return orig_action(self, action)

Game.begin_action = begin_action

g.run_until_idle(max_steps=6000, chooser=bot.choose)

for d, h, a, gold in day_actions:
    print(f'day {d:3} hex {h} action {a:10} gold before {gold}')
print(f'final: day {g.day} gold {g.gold} staff {g.staff} reason {g.reason}')
print('visited places:', [(h, g.place_kind(h)) for h in g.visited
                          if g.place_kind(h)])
