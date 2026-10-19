"""Rebuild data/events.json from the raw events.doc dump, recovering every section.

The original events.json merged some sections into their predecessor (e003, e005,
e007, e008, e012, e050, e053, e055, e101, e160-e179 were missing). Section headers
in the raw dump sit on their own line as "eNNN Title".
"""
import json
import re

RAW = open('events_raw.txt', encoding='latin-1').read()
RAW = re.sub(r'[^\x20-\x7e\r\n]+', ' ', RAW)
# Some section headers were glued to the end of the previous paragraph.
RAW = re.sub(r'(?<=[.!?])\s+(?=e\d{3}\s+[A-Z])', '\n', RAW)
RAW = re.sub(r'\n\s*\n', '\n', RAW)
lines = RAW.splitlines()


HDR = re.compile(r'^\s*(e\d{3})\s+(.*)$')
headers = [(i, m.group(1), m.group(2).strip())
           for i, l in enumerate(lines) if (m := HDR.match(l))]
print('header lines found:', len(headers))

events = {}
for k, (i, code, title) in enumerate(headers):
    body_lines = lines[i + 1: headers[k + 1][0]] if k + 1 < len(headers) else lines[i + 1:]
    body = ' '.join(l.strip() for l in body_lines if l.strip())
    body = re.sub(r'\s+', ' ', body).strip()
    if code in events:
        events[code]['text'] += ' ' + title + ' ' + body
    else:
        events[code] = {'code': code, 'title': title, 'text': body}

# Sections whose header line was glued to the previous paragraph.
GLUE = re.compile(r'\s(e\d{3})\s+([A-Z][A-Za-z ,\'\-&!]{2,40})\n')
for m in list(GLUE.finditer(RAW)):
    code = m.group(1)
    if code in events:
        continue
    events[code] = {'code': code, 'title': m.group(2).strip(), 'text': ''}

json.dump(events, open('../data/events.json', 'w', encoding='utf-8'), indent=1)
print('events:', len(events))
print('missing codes:', [f'e{i:03d}' for i in range(1, 196)
                        if f'e{i:03d}' not in events and not (167 <= i <= 179)])
print('empty text:', [k for k, v in events.items() if not v['text']])
print('no title:', [k for k, v in events.items() if not v['title']])

