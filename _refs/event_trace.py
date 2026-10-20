"""Trace a handful of problem events through the engine."""
import sys
import traceback

sys.path.insert(0, "src")
from game_model import GameModel
from engine import Game

model = GameModel.load()

for code, roll, choice in [("e007", 7, 0), ("e007", 8, 2), ("e098", 3, 0),
                           ("e021", 6, 0)]:
    print("=" * 70)
    print(code, "roll", roll, "choice", choice)
    g = Game(model=model, seed=7)
    g.d1 = lambda r=roll: r
    try:
        g.encounter(code)
        steps = 0
        while g.is_busy() and steps < 20 and not g.game_over:
            p = g.current()
            print("  prompt:", p["title"], "|", [o["label"] for o in p["options"]])
            g.answer(0 if steps == 0 else min(choice, len(p["options"]) - 1))
            steps += 1
    except Exception:
        traceback.print_exc()
    for line in g.log[-12:]:
        print("   log:", line)
