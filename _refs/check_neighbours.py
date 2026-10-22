import sys
sys.path.insert(0, 'src')
from geometry import neighbours, hex_id, parse_hex, NC, NR

errors = []
for col in range(1, NC + 1):
    for row in range(1, NR + 1):
        for d, n in neighbours(col, row).items():
            nc, nr = parse_hex(n)
            if hex_id(col, row) not in neighbours(nc, nr).values():
                errors.append(f'{hex_id(col,row)}->{n} not reciprocal')

if errors:
    print(f'{len(errors)} errors:')
    for e in errors[:20]:
        print(f'  {e}')
else:
    print('all reciprocal')