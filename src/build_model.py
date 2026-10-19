"""Assemble the validated map grid, rules, tables and events into one model.

Reads:
  _refs/hexes.json          terrain classification for all 460 hexes
  data/rules.json           rule sections r201-r343
  data/tables.json          every structured table
  data/events.json          event sections e001-e195 (e167-e179 do not exist)
  data/event_options.json   encounter option matrices

Writes:
  data/game_model.json      unified model
  data/validation_report.txt integrity findings
"""
import json
import os
import re
from collections import Counter, defaultdict

from geometry import (NC, NR, R, DX, DY, SCANS, TERRAIN_TO_TRAVEL, MOVEMENT_MODES,
                      centre, best_scan, neighbours)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
REFS = os.path.join(ROOT, '_refs')


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_grid(hexes):
    grid = {}
    for h in hexes:
        col, row = h['col'], h['row']
        scan = best_scan(col, row)
        cx, cy = centre(col, row, scan)
        grid[h['id']] = {
            'id': h['id'],
            'col': col,
            'row': row,
            'terrain': h['terrain'],
            'travel_terrain': TERRAIN_TO_TRAVEL.get(h['terrain'], 'Countryside'),
            'confidence': round(1.0 - min(h['dist'], 100) / 100.0, 3),
            'neighbors': neighbours(col, row),
            'scan': scan,
            'center': [round(cx, 1), round(cy, 1)],
        }
    return grid


REF_RE = re.compile(r'\b([re]\d{3})\b')

# Sections that live in the separate tables sheet rather than rules.doc.
TABLE_REFS = {'r207': 'travel_table', 'r230': 'raft_travel_events',
              'r281': 'special_travel_reference'}
TABLE_REFS.update({f'r{n}': 'travel_event_refs' for n in range(231, 281)})

# The booklet states "sections r229 and r282-299 do not exist".
NONEXISTENT = {'r229'} | {f'r{n}' for n in range(282, 300)}
NONEXISTENT |= {f'e{n:03d}' for n in range(167, 180)}
# The booklet contains a handful of misprinted section numbers. Each of these
# appears in the text but has no corresponding section; the correction is
# inferred from context (r143 is confirmed by the errata sheet).
REFERENCE_FIXES = {
    'e226': 'e026',   # raft table row 2 -> Search for Treasure
    'e250': 'e050',   # temple audience row 9 -> Local Constabulary
    'e341': 'r341',   # "see e341" -> Conversation Results
    'r119': 'r319',   # e005 option table row 4 -> Hide
    'r143': 'r341',   # errata: e076 victim selection should be r341
}




def build_index(grid, rules, tables, events, options):
    """Where every rNNN / eNNN reference is mentioned."""
    mentions = defaultdict(set)

    def scan(text, source):
        for m in REF_RE.finditer(text or ''):
            mentions[m.group(1)].add(source)

    for rid, sec in rules.items():
        scan(sec['text'], f'rule:{rid}')
        scan(sec['title'], f'rule:{rid}')
    for code, ev in events.items():
        scan(ev['text'], f'event:{code}')
    for name, val in tables.items():
        scan(json.dumps(val), f'table:{name}')
    for code, opt in options.items():
        scan(json.dumps(opt), f'option:{code}')

    hex_events = defaultdict(set)
    for code, ev in events.items():
        for m in re.finditer(r'\b(\d{4})\b', ev['text']):
            hid = m.group(1)
            if hid in grid:
                hex_events[hid].add(code)

    return mentions, hex_events


def validate(grid, rules, tables, events, options, mentions):
    problems = []

    if len(grid) != NC * NR:
        problems.append(f'grid has {len(grid)} hexes, expected {NC * NR}')

    for hid, h in grid.items():
        for d, n in h['neighbors'].items():
            if n not in grid:
                problems.append(f'{hid} neighbor {d}={n} missing from grid')

    known = set(rules) | set(events) | set(TABLE_REFS)
    dangling = sorted(r for r in mentions
                      if r not in known and r not in NONEXISTENT)
    typos = [r for r in dangling if r in REFERENCE_FIXES]
    dangling = [r for r in dangling if r not in REFERENCE_FIXES]
    if typos:
        problems.append(f'{len(typos)} misprinted references corrected: '
                        + ', '.join(f'{k}->{v}' for k, v in sorted(REFERENCE_FIXES.items())))
    if dangling:
        problems.append(f'{len(dangling)} references point at sections that were '
                        f'not extracted: {", ".join(dangling[:40])}')

    travel = {row['terrain'] for row in tables['travel_table']}
    missing_modes = set(MOVEMENT_MODES) - travel
    if missing_modes:
        problems.append(f'travel table missing movement rows: {missing_modes}')

    for row in tables['travel_table']:
        for ref in row.get('event_refs', []):
            if ref.startswith('e') and ref not in events:
                problems.append(f'travel row {row["terrain"]} -> {ref} not in events')

    for code, opt in options.items():
        for r in opt['rows']:
            for cell in r['cells']:
                ref = cell['ref']
                if ref and ref not in known:
                    fixed = REFERENCE_FIXES.get(ref)
                    if fixed and fixed in known:
                        cell['ref_fixed'] = fixed
                    else:
                        problems.append(f'{code} option roll {r["roll"]} -> {ref} unresolved')

    unreachable = sorted(set(events) - {r for r in mentions if r.startswith('e')})
    return problems, dangling, unreachable


def ref_context(ref, rules, events, tables):
    """First few places a reference appears, to help judge whether it is a typo."""
    hits = []
    for rid, sec in rules.items():
        for m in re.finditer(re.escape(ref), sec['text']):
            hits.append(f'{rid}: ...{sec["text"][max(0, m.start() - 60):m.end() + 40]}...')
    for code, ev in events.items():
        for m in re.finditer(re.escape(ref), ev['text']):
            hits.append(f'{code}: ...{ev["text"][max(0, m.start() - 60):m.end() + 40]}...')
    return hits[:3]


def main():
    hexes = load(os.path.join(REFS, 'hexes.json'))
    rules = load(os.path.join(DATA, 'rules.json'))
    tables = load(os.path.join(DATA, 'tables.json'))
    events = load(os.path.join(DATA, 'events.json'))
    options = load(os.path.join(DATA, 'event_options.json'))

    grid = build_grid(hexes)
    mentions, hex_events = build_index(grid, rules, tables, events, options)
    problems, dangling, unreachable = validate(grid, rules, tables, events, options, mentions)

    model = {
        'meta': {
            'board': 'BarbarianPrince',
            'hexes': len(grid),
            'columns': NC,
            'rows': NR,
            'rule_sections': len(rules),
            'events': len(events),
            'event_option_tables': len(options),
            'tables': sorted(tables),
        },
        'geometry': {
            'orientation': 'flat-top',
            'radius_px': R,
            'dx_px': round(DX, 3),
            'dy_px': round(DY, 3),
            'columns': NC,
            'rows': NR,
            'scans': SCANS,
        },
        'grid': grid,
        'rules': rules,
        'tables': tables,
        'events': events,
        'event_options': options,
        'index': {
            'ref_mentions': {r: sorted(s) for r, s in sorted(mentions.items())},
            'hex_events': {h: sorted(e) for h, e in sorted(hex_events.items())},
            'dangling_refs': dangling,
            'reference_fixes': REFERENCE_FIXES,
            'unreferenced_events': unreachable,
        },
    }

    with open(os.path.join(DATA, 'game_model.json'), 'w', encoding='utf-8') as f:
        json.dump(model, f, indent=1)

    lines = [
        f'hexes: {len(grid)}  rules: {len(rules)}  events: {len(events)}  '
        f'option tables: {len(options)}',
        'terrain counts: ' + ', '.join(
            f'{t}={c}' for t, c in Counter(h['terrain'] for h in grid.values()).most_common()),
        f'low-confidence terrain: {sum(1 for h in grid.values() if h["confidence"] < 0.4)}',
        f'misprinted refs corrected ({len(REFERENCE_FIXES)}): '
        + ', '.join(f'{k}->{v}' for k, v in sorted(REFERENCE_FIXES.items())),
        f'dangling refs ({len(dangling)}): {", ".join(dangling)}',
        f'events never referenced ({len(unreachable)}): {", ".join(unreachable)}',
        f'hexes named by events: {len(hex_events)}',
        '',
        'UNRESOLVED REFERENCE CONTEXT:',
    ]
    for ref in dangling:
        for h in ref_context(ref, rules, events, tables):
            lines.append('  ' + ref + ' <- ' + h)
    lines.append('')
    lines.append('PROBLEMS:')
    lines.extend('  ' + p for p in problems)
    report = '\n'.join(lines)
    with open(os.path.join(DATA, 'validation_report.txt'), 'w', encoding='utf-8') as f:
        f.write(report)
    print(report)


if __name__ == '__main__':
    main()

