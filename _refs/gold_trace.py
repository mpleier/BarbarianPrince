import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import engine
from engine import Game
from autoplay import Bot

orig_note = engine.Game.note

def note(self, text):
    low = text.lower()
    if 'gold' in low or 'loot' in low:
        self._goldlog.append((self.day, self.hex, text))
    return orig_note(self, text)

engine.Game.note = note

for seed in range(1, 6):
    g = Game(seed=seed)
    g._goldlog = []
    bot = Bot(g, 'balanced')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    print(f'=== seed {seed}: day {g.day} gold {g.gold} staff {g.staff} '
          f'reason {g.reason}')
    for d, h, t in g._goldlog:
        print(f'  day {d} {h}: {t}')
