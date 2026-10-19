import json

d = json.load(open('../data/tables.json', encoding='utf-8'))
out = []
for name in ('audience', 'news', 'offerings', 'hiring', 'conversation', 'general_inquiry',
             'battle_reference', 'combat_table', 'treasure_table', 'cache_recovery',
             'trap_locks', 'ruins_search', 'special_possession_lines', 'raft_travel_events'):
    out.append(f'=== {name} ===')
    out.append(json.dumps(d[name], indent=1))
open('tables_dump.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', sum(len(x) for x in out))
