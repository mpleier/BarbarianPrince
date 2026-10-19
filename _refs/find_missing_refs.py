import glob
import re

pat = re.compile(r'\br(2[0-9]{2})\b')
found = {}
for f in glob.glob('*.txt'):
    t = open(f, encoding='latin-1', errors='replace').read()
    for m in pat.finditer(t):
        found.setdefault(int(m.group(1)), set()).add(f)

want = list(range(229, 300))
print('sections 229-299 found in:')
for n in want:
    if n in found:
        print(n, sorted(found[n]))
print('---- missing:', [n for n in want if n not in found])
