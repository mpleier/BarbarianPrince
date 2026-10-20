import json

f = json.load(open('data/features.json'))
places = f['places']
kinds = {}
for hid, p in places.items():
    kinds.setdefault(p['kind'], []).append(hid)
for k, v in sorted(kinds.items()):
    print(k, len(v), v[:12])
