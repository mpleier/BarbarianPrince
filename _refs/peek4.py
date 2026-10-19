import json
d = json.load(open('../data/tables.json', encoding='utf-8'))
for r in d['travel_table']:
    print(r['terrain'], '|', r['lost'], '|', r['event_threshold'], '|', ' '.join(r['event_refs']), '|', r['hunt'], r['fodder'])
print()
for k, v in d['audience'].items():
    print('---', k, v['hex'], '| note:', v['note'][:60])
    for row in v['rows']:
        print('   ', row['roll'], '->', row['text'][:70])
print()
print('news rows:', len(d['news']))
for r in d['news']:
    print('  ', r['roll'], '->', r['text'][:60])
print()
print('hiring rows:', len(d['hiring']))
for r in d['hiring']:
    print('  ', r['roll'], '->', r['text'][:60])
print()
print('offerings rows:', len(d['offerings']))
for r in d['offerings']:
    print('  ', r['roll'], '->', r['text'][:60])
