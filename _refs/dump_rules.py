import re, sys

SRC = 'rules_clean.txt'
lines = open(SRC, encoding='latin-1').read().splitlines()

# locate section starts
starts = []
for i, l in enumerate(lines):
    m = re.match(r'\s*(r\d{3})\b', l)
    if m:
        starts.append((m.group(1), i))

idx = {r: i for r, i in starts}
print('sections found:', len(starts))

def dump(a, b):
    for i in range(a, b):
        s = lines[i].strip()
        if s:
            print(f'{i+1}| {s}')

for r, i in starts:
    if r in ('r201', 'r202', 'r203', 'r204', 'r205', 'r206', 'r208', 'r209', 'r210',
            'r211', 'r212', 'r213', 'r214', 'r215', 'r216', 'r217', 'r218', 'r219',
            'r220', 'r221', 'r222', 'r225', 'r226', 'r227', 'r228'):
        nxt = [j for rr, j in starts if rr > r]
        dump(i, min(nxt[:1], [i + 60])[0])
        print('---')
