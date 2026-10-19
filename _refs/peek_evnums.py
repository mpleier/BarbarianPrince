import re
from collections import Counter

txt = open('events.txt', encoding='utf-8', errors='replace').read()
hits = re.findall(r'\b\d{4}\b', txt)
print(Counter(hits).most_common(60))
print()
for mm in re.finditer(r'.{50}\b\d{4}\b.{50}', txt):
    s = mm.group(0).replace('\n', ' ')
    print(s)