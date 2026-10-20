"""Optimal ruin-farming duration R for a given total time T (ruin + travel + camp)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '_refs')
from camp_policy import camp

RUIN = 5.64
print(f'{"T":>4} {"travel":>7} {"R*":>4} {"C*":>4} {"gold":>6} {"win":>7}')
for T in (40, 45, 50, 55, 60, 65):
    for travel in (6, 8, 10, 12):
        best = (-1, 0)
        for R in range(0, T - travel + 1):
            C = T - travel - R
            v = camp(C, min(400, int(RUIN * R)), 0, 0, 0)[0]
            if v > best[0]:
                best = (v, R)
        v, R = best
        print(f'{T:>4} {travel:>7} {R:>4} {T-travel-R:>4} {min(400,int(RUIN*R)):>6} {v:>7.4f}')
