import re
ls = open('tables_raw.txt', encoding='latin-1').read().splitlines()
print('lines:', len(ls))
for i, l in enumerate(ls):
    if l.strip():
        print(i + 1, '|', l[:160])
