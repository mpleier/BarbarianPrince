"""Inspect the structure of the generated hex model files."""
import json

h = json.load(open("hexes.json"))
print("hexes.json:", len(h), "entries")
print(json.dumps(h[0], indent=1))
print(json.dumps(h[1], indent=1))

try:
    s = json.load(open("hexsides.json"))
    print("\nhexsides.json:", len(s))
    print(json.dumps(s[:3], indent=1))
except Exception as e:
    print("hexsides:", e)
