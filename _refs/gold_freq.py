import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import engine
from engine import Game
from autoplay import Bot

orig_note = engine.Game.note

def note(self, text):
    low = text.lower()
    if 'gold' in low or 'loot' in low or 'wealth' in low:
        self._goldlog.append(text)
    return orig_note(self, text)

engine.Game.note = note

from collections import Counter
c = Counter()
for seed in range(1, 31):
    g = Game(seed=seed)
    g._goldlog = []
    bot = Bot(g, 'aggressive')
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    for t in g._goldlog:
        c[t[:60]] += 1
    if seed <= 3:
        print(f'--- seed {seed} gold {g.gold}')
        for t in g._goldlog:
            print('   ', t)
print('=== gold-related note frequency (30 seeds, aggressive) ===')
for k, v in c.most_common(40):
    print(f'{v:4}  {k}')
