import sys
sys.path.insert(0, 'src')
from engine import parse_options
import json

e = json.load(open('data/events.json'))
for c in ['e003', 'e050', 'e100', 'e006']:
    r = parse_options(e[c]['text'])
    print(c, '->', r[0] if r else None)
    if r:
        for roll, cells in r[1][:3]:
            print('   roll', roll, cells)
