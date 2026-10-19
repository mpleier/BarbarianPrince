import re

for f in ('rules_sections.txt', 'tables_clean.txt', 'errata.txt', 'events_raw.txt'):
    t = open(f, encoding='latin-1').read()
    for tag in ('r229', 'r230', 'r281', 'r282', 'e226', 'e250', 'e341', 'r119'):
        for m in re.finditer(re.escape(tag), t):
            s = max(0, m.start() - 120)
            print(f'{f} {tag}: ...{t[s:m.start() + 60]}...')
            print()
