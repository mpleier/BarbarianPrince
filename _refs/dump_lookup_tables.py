import json

t = json.load(open('data/tables.json', encoding='utf-8'))
for k in ('ruins_search', 'audience', 'offerings', 'raft_travel_events',
          'cache_recovery', 'news'):
    print('===', k)
    v = t[k]
    if isinstance(v, dict):
        for key, val in v.items():
            print('  ', key, '->', str(val)[:140])
    else:
        for r in v:
            print('  ', r.get('roll'), r.get('rolls'), str(r.get('text'))[:140])
