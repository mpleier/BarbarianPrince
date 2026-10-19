"""Extract structured rules/tables for BarbarianPrince from the cleaned text dumps.

Inputs:
  _refs/rules_sections.txt   - section-per-line dump of rules.doc (r201..r343)
  _refs/tables_clean.txt     - cleaned text of tables.doc (Travel Table + r231-r280 refs)
  data/events.json           - already-extracted event sections (e001..)

Outputs:
  data/rules.json            - {section_id: {id, title, text}}
  data/tables.json           - every structured table, keyed by table name
  data/event_options.json    - per-event encounter option matrices
  data/csv/<name>.csv        - one CSV per table
"""
import csv
import json
import os
import re

REFS = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(REFS, '..', 'data'))
CSVD = os.path.join(DATA, 'csv')
os.makedirs(CSVD, exist_ok=True)


def read(path):
    with open(path, encoding='latin-1') as f:
        return f.read()


def roll_table(text):
    """Parse '2-e133; 3-e135; ...' / '2 e125 3 e226 ...' style roll -> ref maps."""
    out = {}
    for m in re.finditer(r'(\d{1,2})\s*(?:\(\s*or\s*(?:less|more)\s*\))?[-:]?\s*([re]\d{3})', text):
        out.setdefault(int(m.group(1)), m.group(2))
    return out


def word_table(text, lo=1, hi=12):
    """Parse '2 <result text> 3 <result text> ...' into {int: text}."""
    out = {}
    toks = text.split()
    idx = [i for i, t in enumerate(toks) if re.match(r'^\d{1,2}$', t) and lo <= int(t) <= hi]
    for k, i in enumerate(idx):
        end = idx[k + 1] if k + 1 < len(idx) else len(toks)
        out[int(toks[i])] = ' '.join(toks[i + 1:end]).strip()
    return out


ROLLSPEC = re.compile(r'(?<=\s)(\d{1,2}(?:\s*,\s*\d{1,2})*(?:\s*\+|\s*or\s*more|\s*or\s*less)?)(?=\s+[A-Z])')


def range_table(text):
    """Parse '2 <text> 3 <text> 6,7,8 <text> 13+ <text>' into ordered rows."""
    ms = list(ROLLSPEC.finditer(text))
    rows = []
    for k, m in enumerate(ms):
        end = ms[k + 1].start() if k + 1 < len(ms) else len(text)
        spec = m.group(1)
        rolls = [int(x) for x in re.findall(r'\d+', spec)]
        rows.append({'roll': spec.replace(' ', ''),
                     'rolls': rolls,
                     'open_ended': '+' in spec or 'more' in spec,
                     'text': re.sub(r'\s+', ' ', text[m.end():end]).strip()})
    return rows



# ------------------------------------------------------------------ rules text
RAW = read(os.path.join(REFS, 'rules_sections.txt'))
SECTIONS = {}
for line in RAW.splitlines():
    line = line.strip()
    if not line:
        continue
    m = re.match(r'^(r\d{3})\s+(.*)$', line)
    if m:
        SECTIONS[m.group(1)] = {'id': m.group(1), 'title': m.group(2).strip(), 'text': ''}
    elif SECTIONS:
        last = list(SECTIONS)[-1]
        SECTIONS[last]['text'] += ' ' + line

for s in SECTIONS.values():
    s['text'] = re.sub(r'\s+', ' ', s['text'])

# ------------------------------------------------------------------ Travel Table (r207)
RAW_T = read(os.path.join(REFS, 'tables_raw.txt')).splitlines()
travel_line = next(l for l in RAW_T if l.startswith('Terrain type'))
ref_line = next(l for l in RAW_T if 'Die roll Ref. number' in l)
toks = travel_line.split()
TERRAINS = ['Farmland', 'Countryside', 'Forest', 'Hills', 'Mountains', 'Swamp', 'Desert',
            'Cross River', 'On Road', 'Airborne', 'Rafting']

travel_table = []
i = toks.index('Farmland')
for name in TERRAINS:
    i += len(name.split())
    lost = toks[i]; i += 1
    event = toks[i]; i += 1
    refs = []
    while len(refs) < 6 and i < len(toks) and not re.match(r'(yes|no|\*no|-)$', toks[i]):
        if re.match(r'^[er]\d{3}$', toks[i]):
            refs.append(toks[i])
        i += 1
    while len(refs) < 6:
        refs.append('-')
    hunt = toks[i] if i < len(toks) else '-'
    fodder = toks[i + 1] if i + 1 < len(toks) else '-'
    i += 2
    travel_table.append({'terrain': name, 'lost': lost, 'event_threshold': event,
                         'event_refs': refs, 'hunt': hunt, 'fodder': fodder})

raft_line = next(l for l in RAW_T if re.match(r'^\s*2\s+e125', l))
raft_events = roll_table(raft_line)

idx = next((k for k, l in enumerate(RAW_T) if l.startswith('r281')), None)
special_travel = re.sub(r'\s+', ' ', ' '.join(RAW_T[idx + 1:idx + 3])).strip() if idx else ''

event_refs = {}
for m in re.finditer(r'(r2\d{2})\s+((?:e\d{3}\s+){5}e\d{3})', ref_line):
    event_refs[m.group(1)] = m.group(2).split()


# ------------------------------------------------------------------ Combat Table (r220c)
WORD = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6, 'Seven': 7, 'Eight': 8}
combat_table = {}
m = re.search(r'-1,3,5,8,11 One wound.*?Six wounds', SECTIONS['r220']['text'])
if m:
    for g in re.finditer(r'([0-9,\-]+)\s+(One|Two|Three|Four|Five|Six|Seven|Eight)\s+wounds?', m.group(0)):
        for n in g.group(1).split(','):
            combat_table[int(n)] = WORD[g.group(2)]

# ------------------------------------------------------------------ Treasure Table (r226)
ttoks = SECTIONS['r226']['text'].split()
i = ttoks.index('6') + 1
treasure_table = []
possessions = {}
while i < len(ttoks):
    t = ttoks[i]
    if t in ('A', 'B', 'C'):
        possessions[t] = ttoks[i + 1:i + 7]
        i += 7
        continue
    if re.match(r'^\d+$', t):
        code = int(t)
        if code == 0:
            treasure_table.append({'code': 0, 'results': [0] * 6,
                                   'note': 'Character has no gold or possessions'})
            i += 1
            while i < len(ttoks) and not re.match(r'^(\d+|[ABC])$', ttoks[i]):
                i += 1
        else:
            treasure_table.append({'code': code, 'results': ttoks[i + 1:i + 7]})
            i += 7
    else:
        i += 1

# ------------------------------------------------------------------ roll -> result tables
ruins = roll_table(SECTIONS['r208']['text'])
news = range_table(SECTIONS['r209']['text'])
hiring = range_table(SECTIONS['r210']['text'])
offerings = range_table(SECTIONS['r212']['text'])
cache = range_table(SECTIONS['r214']['text'])
traps = range_table(SECTIONS['r227']['text'])
battle_ref = roll_table(SECTIONS['r330']['text'])
conversation = range_table(SECTIONS['r341']['text'])
inquiry = range_table(SECTIONS['r342']['text'])

# ------------------------------------------------------------------ audience tables (r211)
aud = SECTIONS['r211']['text']
AUD = re.compile(r'Seeking an Audience (?:at|with) ([A-Za-z][A-Za-z ]*?)(?:\s*\((\d{4})\))?(?=\s*(?:Note:|:|\s\d))')
hits = list(AUD.finditer(aud))
audience = {}
for k, h in enumerate(hits):
    end = hits[k + 1].start() if k + 1 < len(hits) else len(aud)
    blk = aud[h.end():end]
    note = ''
    mnote = re.match(r'\s*Note:\s*(.*?)(?=\s\d{1,2}\s*,?\s*(?:or\s*more|or\s*less)?\s+[A-Z])', blk)
    if mnote:
        note = mnote.group(1).strip()
        blk = blk[mnote.end():]
    audience[h.group(1).strip()] = {'hex': h.group(2) or '', 'note': note,
                                    'rows': range_table(blk)}



# ------------------------------------------------------------------ numeric constants
constants = {
    'game_length_days': 70,
    'gold_needed_to_win': 500,
    'prince': {'name': 'Cal Arath', 'combat_skill': 8, 'endurance': 9, 'wealth_code': 2,
               'wit_and_wiles': '1d6 (1 counts as 2)'},
    'travel_speed': {'foot': 1, 'mounted': 2, 'winged': 3},
    'transport': {'food_unit_loads': 1, 'gold_per_load': 100, 'person_loads': 20,
                  'foot_capacity': 10, 'mount_capacity': 30},
    'food': {'unit_per_man_day': 1, 'mount_units': 2, 'no_water_multiplier': 2,
             'purchase_price': 1, 'meal_price': 1},
    'lodging': {'room_cost': 1, 'people_per_room': 2, 'stable_cost': 1},
    'escape_directions': {1: 'N', 2: 'NE', 3: 'SE', 4: 'S', 5: 'SW', 6: 'NW'},
    'combat_modifiers': [
        {'modifier': 2, 'condition': 'target wounds >= half endurance'},
        {'modifier': -1, 'condition': 'striker has one or more wounds'},
        {'modifier': -1, 'condition': 'striker wounds >= half endurance'},
    ],
    'wounds': {'serious': 'wounds >= ceil(endurance/2)',
               'unconscious': 'wounds == endurance - 1',
               'death': 'wounds >= endurance'},
    'rout_roll': 6,
    'escape_roll': 4,
    'desertion_roll': 4,
    'raft_speed': {'downriver': 3, 'upriver': 2},
}

# ------------------------------------------------------------------ errata (published corrections)
errata = []
for line in read(os.path.join(REFS, 'errata.txt')).splitlines():
    line = re.sub(r'\s+', ' ', line).strip()
    m = re.match(r'^([re]\d{3})\s+(.*)$', line)
    if m:
        errata.append({'section': m.group(1), 'correction': m.group(2)})
    elif errata and line:
        errata[-1]['correction'] += ' ' + line

tables = {
    'travel_table': travel_table,
    'raft_travel_events': raft_events,
    'travel_event_refs': event_refs,
    'special_travel_reference': special_travel,
    'combat_table': combat_table,
    'treasure_table': treasure_table,
    'special_possession_lines': possessions,
    'ruins_search': ruins,
    'news': news,
    'hiring': hiring,
    'offerings': offerings,
    'cache_recovery': cache,
    'trap_locks': traps,
    'battle_reference': battle_ref,
    'conversation': conversation,
    'general_inquiry': inquiry,
    'audience': audience,
    'constants': constants,
    'errata': errata,
}

json.dump(SECTIONS, open(os.path.join(DATA, 'rules.json'), 'w'), indent=1)
json.dump(tables, open(os.path.join(DATA, 'tables.json'), 'w'), indent=1)

for name, val in tables.items():
    with open(os.path.join(CSVD, name + '.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if isinstance(val, list):
            if val and isinstance(val[0], dict):
                cols = sorted({k for row in val for k in row})
                w.writerow(cols)
                for row in val:
                    w.writerow([row.get(c, '') for c in cols])
            else:
                w.writerow(['value'])
                for row in val:
                    w.writerow([row])
        else:
            if isinstance(val, str):
                w.writerow(['value'])
                w.writerow([val])
            else:
                w.writerow(['key', 'value'])
                for k, v in val.items():
                    w.writerow([k, v if isinstance(v, (str, int, float)) else json.dumps(v)])

# ------------------------------------------------------------------ event option matrices
EVENTS = json.load(open(os.path.join(DATA, 'events.json'), encoding='utf-8'))
REF = re.compile(r'^(?:r\d{3}|e\d{3})$')
options = {}
for code, ev in EVENTS.items():
    text = ev['text']
    m = re.search(r'\bdie roll\b', text)
    if not m:
        continue
    toks = text[m.end():].split()
    i = 0
    headers = []
    while i < len(toks) and toks[i] != '1':
        headers.append(toks[i].lstrip('*'))
        i += 1
    if i >= len(toks) or toks[i] != '1':
        continue
    rows = []
    want = 1
    while i < len(toks) and want <= 6 and toks[i] == str(want):
        j = i + 1
        start = j
        cells = []
        while j < len(toks) and toks[j] != str(want + 1):
            if REF.match(toks[j]):
                cells.append({'label': ' '.join(toks[start:j]).strip(), 'ref': toks[j]})
                start = j + 1
            j += 1
        if start < j:
            cells.append({'label': ' '.join(toks[start:j]).strip(), 'ref': None})
        rows.append({'roll': want, 'cells': cells})
        i = j
        want += 1
    if rows:
        options[code] = {'title': ev['title'], 'columns': headers, 'rows': rows}

json.dump(options, open(os.path.join(DATA, 'event_options.json'), 'w'), indent=1)

print('rule sections:', len(SECTIONS))
print('travel rows:', len(travel_table))
print('travel event refs:', len(event_refs))
print('combat totals:', len(combat_table))
print('treasure codes:', len(treasure_table))
print('news:', len(news), '| hiring:', len(hiring), '| offerings:', len(offerings))
print('audience:', list(audience))
print('events with option tables:', len(options))



