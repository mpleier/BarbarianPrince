import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import neighbours, parse_hex

for h in ['0101', '2001', '0123', '2023', '1212', '1313', '1922', '2022']:
    print(h, neighbours(*parse_hex(h)))

