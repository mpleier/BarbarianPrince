import json

d = json.load(open('../data/tables.json', encoding='utf-8'))
print('=== travel_table ===')
for r in d['travel_table']:
    print(r['terrain'], '| lost', r['lost'], '| event', r['event_threshold'],
          '| refs', r['event_refs'], '| hunt', r['hunt'], '| fodder', r['fodder'])
print('=== event_refs ===')
print('count:', len(d['travel_event_refs']))
bad = {k: v for k, v in d['travel_event_refs'].items() if len(v) != 6}
print('bad rows:', bad)
print('=== raft ===')
print(d['raft_travel_events'])
print('=== constants ===')
print(json.dumps(d['constants'], indent=1))
