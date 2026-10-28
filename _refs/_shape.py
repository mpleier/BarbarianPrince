import json
t = json.load(open('data/tables.json', encoding='utf-8'))
for k in ['combat_table', 'battle_reference', 'ruins_search', 'raft_travel_events']:
    v = t[k]
    if isinstance(v, dict):
        print(f'{k} (dict): { {str(a):b for a,b in list(v.items())[:14]} }')
    else:
        print(f'{k}: {json.dumps(v[:3])}')
print()
print('conversation[0:3]:', json.dumps(t['conversation'][:3]))
print('general_inquiry[0:2]:', json.dumps(t['general_inquiry'][:2]))
print()
print('special_possession_lines:', json.dumps(t['special_possession_lines'])[:200])
print('constants:', json.dumps(t['constants'])[:300])
print()
# audience shape
aud = t['audience']
for name, entry in aud.items():
    print('audience', name, 'keys:', list(entry.keys()),
          '| rows len:', len(entry.get('rows', [])),
          '| row0:', json.dumps(entry.get('rows', [{}])[0])[:120])
