"""Dump every rule/tables fragment that mentions rafting, plus the Rafting row
of the Travel Table (r207) and the daily-action list (r203)."""
import json
import re

rules = json.load(open("data/rules.json", encoding="utf-8"))
tables = json.load(open("data/tables.json", encoding="utf-8"))

print("=== rules mentioning 'raft' ===")
for rid, r in sorted(rules.items()):
    text = r.get("text", "")
    if "raft" in text.lower():
        print(f"\n--- {rid}: {r.get('title')} ---")
        print(text)

print("\n=== r203 (daily actions) ===")
print(rules.get("r203", {}).get("title"))
print(rules.get("r203", {}).get("text"))

print("\n=== travel table rows (r207) ===")
for name, row in tables.get("travel_event_refs", {}).items():
    print(name, "| lost:", row.get("lost"), "| threshold:", row.get("event_threshold"),
          "| refs:", row.get("event_refs"))

print("\n=== raft_travel_events ===")
print(tables.get("raft_travel_events"))

print("\n=== keys in tables.json ===")
print(sorted(tables.keys()))
