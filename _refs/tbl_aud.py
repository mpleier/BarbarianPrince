import sys, json
sys.path.insert(0, 'src')
m = json.load(open('data/game_model.json', encoding='utf-8'))
print('=== AUDIENCE (r211) ===')
for key, entry in m['tables']['audience'].items():
    print('---', key)
    for r in entry['rows']:
        print('  ', r['roll'], '|', r['text'])
print()
print('=== RUINS (r208) ===')
print(m['tables'].get('ruins'))
print()
print('=== TREASURE (r226) first 12 ===')
for r in m['tables']['treasure_table'][:12]:
    print(r)
