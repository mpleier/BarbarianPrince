"""Full text of the raft-granting events and the Rafting row of the travel table."""
import json

events = json.load(open("data/events.json", encoding="utf-8"))
tables = json.load(open("data/tables.json", encoding="utf-8"))

for code in ("e122", "e123", "e124", "e125", "e126", "e127"):
    ev = events.get(code)
    if ev:
        print(f"--- {code}: {ev['title']} ---")
        print(ev["text"])
        print()

print("=== travel_table structure ===")
tt = tables["travel_table"]
print(type(tt))
if isinstance(tt, dict):
    for k, v in tt.items():
        print(k, "->", v)
else:
    for row in tt:
        print(row)
