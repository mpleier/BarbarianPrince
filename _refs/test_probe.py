import sys
sys.path.insert(0, 'src')
from camp_dp import camp_value, camp_action, ruin_gold_target

print('camp_value(days, gold, perm=0):')
for days in (5, 10, 12, 15, 19, 25, 30, 40, 46, 55):
    for gold in (20, 40, 65, 100, 145, 200):
        print(f'  days={days:>3} gold={gold:>4} -> {camp_value(days, gold, 0, 0, 0, False):.4f}')
print()
print('ruin_gold_target(days, travel=10):')
for days in (20, 30, 40, 46, 50, 55, 60):
    print(f'  days={days:>3} -> {ruin_gold_target(days, 10)}')
print()
print('camp_value with perm=1, days=12, gold=65:', camp_value(12, 65, 1, 0, 0, False))


