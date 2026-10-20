import json

d = json.load(open('data/tables.json'))
aud = d['audience']
print('audience type:', type(aud))
if isinstance(aud, dict):
    for k, v in aud.items():
        print(k, '->', str(v)[:120])
else:
    for r in aud:
        print(r)
