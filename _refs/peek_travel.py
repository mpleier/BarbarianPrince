import re

raw = open('tables_raw.txt', encoding='latin-1').read().splitlines()
line = next(l for l in raw if l.startswith('Terrain type'))
toks = line.split()
print(len(toks))
print(toks)
