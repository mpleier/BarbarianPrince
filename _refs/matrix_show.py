"""Print the parsed option matrix for a few events."""
import sys

sys.path.insert(0, "src")
from game_model import GameModel
from engine import parse_options

model = GameModel.load()
for code in ("e020", "e112", "e002", "e130", "e005", "e100", "e021", "e007"):
    headers, rows, note = parse_options(model.events[code]["text"])
    print("==", code, model.events[code]["title"])
    print("   headers:", headers)
    for roll, cells in rows:
        print("   ", roll, cells)
    print("   note:", note[:120])
