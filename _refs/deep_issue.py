"""Deep analysis of model issues found so far."""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'data')

with open(os.path.join(DATA, 'features.json'), encoding='utf-8') as f:
    feats = json.load(f)

rs_set = {frozenset(p) for p in feats['river_sides']}
rds_set = {frozenset(p) for p in feats['road_sides']}

def is_adj(a, b):
    ca, ra = int(a[:2]), int(a[2:])
    cb, rb = int(b[:2]), int(b[2:])
    ia, ja = ca-1, ra-1
    ib, jb = cb-1, rb-1
    if ia == ib and ja == jb: return False
    if ia % 2 == 0:
        n = [(ia+1, ja-1),(ia+1, ja),(ia-1, ja-1),(ia-1, ja),(ia, ja-1),(ia, ja+1)]
    else:
        n = [(ia+1, ja),(ia+1, ja+1),(ia-1, ja),(ia-1, ja+1),(ia, ja-1),(ia, ja+1)]
    return (ib, jb) in n

print("=" * 60)
print("ISSUE 1: Invalid river connections (non-adjacent hexes)")
print("=" * 60)
invalid_rivers = []
for a, b in feats['river_sides']:
    if not is_adj(a, b):
        invalid_rivers.append((a, b))
        print(f"  ✗ {a}|{b}")
if not invalid_rivers:
    print("  None found ✓")

print("\n" + "=" * 60)
print("ISSUE 2: Huldra Castle (1212) road disconnection")
print("=" * 60)
# Check what roads connect to 1212 and neighbors
for h in ['1212', '1112', '1213', '1211', '1113', '1313']:
    rd_edges = [(a,b) for a,b in feats['road_sides'] if a==h or b==h]
    in_road_hex = h in feats['road_hexes']
    print(f"  {h}: in road_hexes={in_road_hex}, edges={rd_edges}")

print("\n" + "=" * 60)
print("ISSUE 3: Nesser River upstream gap (0806→1005)")
print("=" * 60)
# The map shows Nesser flowing from 0806 area through to 1005
# Check what's in between
print("  River edges near 0806-1005 area:")
for a, b in feats['river_sides']:
    if int(a[:2]) >= 7 and int(a[:2]) <= 11 and int(a[2:]) >= 5 and int(a[2:]) <= 8:
        print(f"    {a}|{b}")
print("\n  River edges near 1005-1007 area:")
for a, b in feats['river_sides']:
    if int(a[:2]) >= 9 and int(a[:2]) <= 11 and int(a[2:]) >= 4 and int(a[2:]) <= 8:
        print(f"    {a}|{b}")

print("\n" + "=" * 60)
print("ISSUE 4: Argos River southward gap")
print("=" * 60)
print("  River edges in 18xx-20xx area:")
for a, b in feats['river_sides']:
    if int(a[:2]) >= 17 and int(a[:2]) <= 20 and int(a[2:]) >= 13 and int(a[2:]) <= 18:
        print(f"    {a}|{b}")

print("\n" + "=" * 60)
print("FULL DISCREPANCY SUMMARY")
print("=" * 60)
print("""
Based on comparison with barbarianprince_onepiecemap-revc.jpg:

1. INVALID: River edge 1122|1223 - these hexes are NOT adjacent
   Fix: Replace with 1122|1222

2. MISSING: Huldra Castle (1212) not connected to road network
   - 1212 is NOT in road_hexes
   - No road edges connect to 1212
   - Map shows road entering Huldra Castle from NW (1112→1212)
   - Map shows road leaving Huldra Castle to SE (1212→1213 or 1212→1313)

3. MISSING: Nesser upstream connections (0806→1005)
   - Gap between river at 0810/0709 area and 1005 center
   - Need to trace: 0806→0906→1005 or 0807→0907→1006→1005

4. MISSING: Argos River southward extension
   - River stops at 1816 on map, should continue south
   - Need edges: 1913|1914, 1914|2014, etc.
""")
