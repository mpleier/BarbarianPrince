"""Print the reconstructed terrain grid as text for eyeball verification."""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import NC, NR, hex_id

LETTER = {'farmland': '.', 'countryside': ',', 'forest': '#', 'mountains': '^',
          'hills': 'H', 'badlands': 'B', 'swamp': '~', 'desert': 'D', 'unknown': '?'}

hexes = json.load(open('_refs/hexes.json'))
d = {h['id']: h['terrain'] for h in hexes}
for row in range(1, NR + 1):
    line = ''.join(LETTER.get(d[hex_id(c, row)], '?') for c in range(1, NC + 1))
    print(line + '   row ' + str(row))