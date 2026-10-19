import re
t = open('events.txt', encoding='latin-1').read()
print('chars:', len(t))
ms = list(re.finditer(r'e(\d{3})\s+([A-Z][a-z][A-Za-z ,\'-]{2,40})\s', t))
print('candidate titles:', len(ms))
seen = set()
for m in ms[:40]:
    print(m.group(1), '|', m.group(2), '| ctx:', repr(t[max(0, m.start()-40):m.start()]))
