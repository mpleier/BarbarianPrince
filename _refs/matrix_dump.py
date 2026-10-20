"""Dump every encounter option matrix as the engine sees it."""
import json
import sys

sys.path.insert(0, "src")
from engine import parse_options  # noqa: E402

model = json.load(open("data/game_model.json", encoding="utf-8"))
opts = model["event_options"]

print("=== structured event_options.json ===")
for code, table in sorted(opts.items()):
    print(code, table["columns"])
    for row in table["rows"]:
        cells = [(c["label"][:24], c["ref"]) for c in row["cells"]]
        print("   ", row["roll"], cells)

print("\n=== engine parse_options() ===")
for code, ev in sorted(model["events"].items()):
    parsed = parse_options(ev["text"])
    if not parsed:
        continue
    headers, rows, note = parsed
    print(code, headers)
    for roll, cells in rows:
        print("   ", roll, [(lab[:24], ref) for lab, ref in cells])
