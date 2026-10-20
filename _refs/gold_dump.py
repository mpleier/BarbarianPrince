import json
import re

t = json.load(open('data/tables.json'))
e = json.load(open('data/events.json'))
evs = e['events']

gold_re = re.compile(r'\b(\d+)\s+gold', re.I)
hits = []
for code, ev in evs.items():
    text = ev['text']
    if 'gain' in text.lower() and 'gold' in text.lower():
        hits.append((code, ev['title'], text[:120]))

print('events mentioning gain gold:', len(hits))
for code, title, text in hits[:25]:
    print(code, '|', title, '|', text)

print('\n--- audience table (any Town) ---')
for row in t['audience']['any Town']['rows']:
    print(row['roll'], row['text'])

print('\n--- news table sample ---')
news = t['news']
print(type(news))
if isinstance(news, dict):
    for k in list(news)[:3]:
        print(k, json.dumps(news[k])[:400])
else:
    print(json.dumps(news)[:600])
