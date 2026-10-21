import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
L = open(r'c:\Users\mplei\OneDrive\Documents\GitHub\BarbarianPrince\_refs\rules_raw.txt',
         encoding='utf-8', errors='replace').read().splitlines()
for i, l in enumerate(L):
    if re.match(r'^\s*(r\d{3})\s+[A-Za-z]', l):
        print(i + 1, l.strip()[:100])
