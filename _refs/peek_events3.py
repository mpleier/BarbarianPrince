import re

t = open('events_raw.txt', encoding='latin-1').read()
out = []
for tag in ('e002', 'e003', 'e005', 'e012', 'e160'):
    i = t.find(tag)
    out.append(f'=== {tag} at {i} ===')
    out.append(repr(t[max(0, i - 250):i + 250]))
open('peek_out.txt', 'w', encoding='utf-8').write('\n\n'.join(out))
print('written')
