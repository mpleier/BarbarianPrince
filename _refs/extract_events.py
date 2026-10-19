"""Rebuild data/events.json from the raw events.doc dump, recovering every section.

The original events.json merged some sections into their predecessor (e003, e005,
e007, e008, e012, e050, e053, e055, e101, e160-e179 were missing). This walks the
raw text in code order and cuts each section at the start of the next one.
"""
import json
import re

RAW = open('events_raw.txt', encoding='latin-1').read()
RAW = re.sub(r'[\r\n]+', ' ', RAW)
RAW = re.sub(r'[^\x20-\x7e]+', ' ', RAW)
RAW = re.sub(r'\s+', ' ', RAW).strip()

# e167-e179 do not exist in the booklet (confirmed by the text itself).
CODES = [i for i in range(1, 196) if not (167 <= i <= 179)]

pos = {}
cursor = 0
for c in CODES:
    tag = f'e{c:03d}'
    m = re.compile(tag + r'\s+(?=[A-Za-z])').search(RAW, cursor)
    if m is None:
        m = re.compile(tag).search(RAW, cursor)
    if m is None:
        continue
    pos[c] = m.start()
    cursor = m.end()

events = {}
for k, c in enumerate(CODES):
    if c not in pos:
        continue
    end = None
    for nxt in CODES[k + 1:]:
        if nxt in pos:
            end = pos[nxt]
            break
    body = RAW[pos[c]:end if end else len(RAW)].strip()
    head = body[len(f'e{c:03d}'):].strip()
    title = ''
    mt = re.match(r'^([A-Za-z][A-Za-z ,\'\-&!]{2,45})(?=[.:;]|\s\d)', head)
    if mt:
        title = mt.group(1).strip()
    events[f'e{c:03d}'] = {'code': f'e{c:03d}', 'title': title, 'text': body}

json.dump(events, open('../data/events.json', 'w', encoding='utf-8'), indent=1)
print('events:', len(events))
print('with option tables:', sum('die roll' in v['text'] for v in events.values()))
print('untitled:', [k for k, v in events.items() if not v['title']][:20])
