"""Verify specific adjacency checks for the map."""
# Hex grid: 20 cols x 23 rows, odd-r offset
# Col 1-20 (i=0-19), Row 1-23 (j=0-22)

def is_adj(a, b):
    """Check if two hexes are adjacent."""
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

# Key discrepancies to verify
print("=== HEX ADJACENCY CHECKS ===")
pairs = [
    # Nesser upstream
    ('1006', '1007', 'Nesser 1006→1007 south'),
    ('0810', '0710', 'Nesser 0810→0710 SW'),
    ('0811', '0611', 'Nesser 0811→0611 W'),
    ('0710', '0611', 'Nesser 0710→0611 W'),
    ('0711', '0611', 'Nesser 0711→0611 W'),
    # Huldra road
    ('1112', '1113', 'Huldra 1112→1113 S'),
    ('1112', '1212', 'Huldra 1112→1212 SE'),
    ('1211', '1212', 'Huldra 1211→1212 S'),
    ('1212', '1213', 'Huldra 1212→1213 E'),
    ('1213', '1313', 'Huldra 1213→1313 E'),
    # Tragoth
    ('1102', '1202', 'Tragoth 1102→1202 E'),
    ('1101', '1102', 'Tragoth 1101→1102 S'),
    # Greater Nesser
    ('1122', '1223', 'G.Nesser 1122→1223 E'),
    ('1122', '1222', 'G.Nesser 1122→1222 E'),
    # Argos
    ('1913', '1914', 'Argos 1913→1914 S'),
    ('1914', '2014', 'Argos 1914→2014 SE'),
]
for a, b, desc in pairs:
    adj = is_adj(a, b)
    print(f"  {a}|{b}: {'adjacent ✓' if adj else 'NOT adjacent ✗'} — {desc}")
