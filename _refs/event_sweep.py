"""Sweep every event in the model through the engine to prove encounters work.

For each event, every option of the encounter is exercised in a fresh game,
and the resulting chain of prompts is played out to completion.  Any prompt
that never terminates, any reference the engine cannot resolve, and any
exception is reported.
"""
import json
import sys

sys.path.insert(0, "src")
from engine import Game, parse_options, die_entries  # noqa: E402
from game_model import GameModel  # noqa: E402

model = GameModel.load()
codes = sorted(model.events)

problems = {}
kinds = {}
option_count = 0

for code in codes:
    ev = model.events[code]
    opts = parse_options(ev["text"])
    if opts:
        kinds["matrix"] = kinds.get("matrix", 0) + 1
    elif die_entries(ev["text"]):
        kinds["die_table"] = kinds.get("die_table", 0) + 1
    else:
        kinds["plain"] = kinds.get("plain", 0) + 1

    choices = range(len(opts[0])) if opts else [0]
    rolls = [r for r, _ in opts[1]] if opts else [1]
    if not opts:
        entries = die_entries(ev["text"])
        if entries:
            rolls = [r for entry in entries for r in entry[0]]
    for choice in choices:
        for roll in rolls:
            option_count += 1
            g = Game(model=model, seed=7)
            g.d1 = lambda roll=roll: roll
            try:
                g.encounter(code)
                steps = 0
                while g.is_busy() and steps < 60 and not g.game_over:
                    p = g.current()
                    if not p or not p["options"]:
                        problems.setdefault("prompt_without_options", []).append((code, p))
                        break
                    g.answer(0 if steps == 0 else min(choice, len(p["options"]) - 1))
                    steps += 1
                unimpl = [l for l in g.log if "not implemented" in l or "not in the booklet" in l
                          or "No entry for a roll" in l or "repeats itself" in l]
                if unimpl:
                    problems.setdefault("unresolved", []).append((code, choice, roll, unimpl[:2]))
                if g.is_busy() and steps >= 60:
                    problems.setdefault("stuck", []).append((code, choice, roll, len(g.prompts)))
            except Exception as exc:
                problems.setdefault("exception", []).append((code, choice, roll, repr(exc)))

print("event kinds:", kinds)
for kind, items in problems.items():
    print("===", kind, len(items))
    for item in items[:40]:
        print("   ", item)
print("checked", len(codes), "events /", option_count, "option paths")

