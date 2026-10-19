import re

t = open('_refs/rules_clean.txt', encoding='utf-8', errors='replace').read()
for k in ['r206', 'r221', 'r222', 'r223', 'r224', 'r225', 'r216', 'r217',
          'r218', 'r219', 'r215', 'r210', 'r211', 'r212', 'r209', 'r208',
          'r213', 'r214', 'r204', 'r205']:
    m = re.search(re.escape(k) + r'\b(.{0,900})', t, re.S)
    body = m.group(1).replace('\n', ' ')[:900] if m else 'NOT FOUND'
    print(k + ': ' + body)
    print('---')
