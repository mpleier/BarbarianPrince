import re
import os

REFS = os.path.dirname(os.path.abspath(__file__))
txt = ''
for f in ['rules_clean.txt', 'events_clean.txt']:
    txt += open(os.path.join(REFS, f), encoding='utf-8').read()

hits = re.findall(r'\b\d{4}\b', txt)
from collections import Counter
print(Counter(hits).most_common(40))
print()
for mm in re.finditer(r'.{60}\b\d{4}\b.{60}', txt):
    print(mm.group(0).replace('\n', ' '))