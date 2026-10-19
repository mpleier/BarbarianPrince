"""Unified hex-grid + rules model for the BarbarianPrince board.

Geometry (verified visually against both board scans, see _refs/gridcheck_full1.png
and _refs/gridcheck_full2.png):
  * flat-top hexes, 20 columns x 23 rows = 460 hexes
  * hex id = CCRR  (column 01-20, row 01-23)
  * hex radius R = 106.0 px in the scans
  * column step DX = 1.5 * R, row step DY = sqrt(3) * R
  * odd columns are shifted down by DY/2
  * map1.jpg holds rows 01-12, map2.jpg holds rows 13-23
"""
import math

SQ3 = math.sqrt(3.0)
R = 106.0
DX = 1.5 * R
DY = SQ3 * R
NC, NR = 20, 23

# (x0, y0) of the centre of column 1 at row `first_row`, per scan.
SCANS = {
    'map1.jpg': {'x0': 377.0, 'y0': 96.0, 'first_row': 1, 'last_row': 12},
    'map2.jpg': {'x0': 377.0, 'y0': 199.0, 'first_row': 13, 'last_row': 23},
}

# Map legend terrain -> terrain name used by the Travel Table (r207).
TERRAIN_TO_TRAVEL = {
    'farmland': 'Farmland',
    'countryside': 'Countryside',
    'forest': 'Forest',
    'hills': 'Hills',
    'badlands': 'Hills',        # the legend prints "Hills/Badlands" as one entry
    'mountains': 'Mountains',
    'swamp': 'Swamp',
    'desert': 'Desert',
}

# Movement modes that are not a hex terrain but still have a Travel Table row.
MOVEMENT_MODES = ['Cross River', 'On Road', 'Airborne', 'Rafting']

SIDE_NAME = ['NE', 'SE', 'S', 'SW', 'NW', 'N']


def hex_id(col, row):
    return f'{col:02d}{row:02d}'


def parse_hex(hid):
    return int(hid[:2]), int(hid[2:])


def in_grid(col, row):
    return 1 <= col <= NC and 1 <= row <= NR


def centre(col, row, scan='map1.jpg'):
    """Pixel centre of a hex in the given scan."""
    p = SCANS[scan]
    i = col - 1
    return (p['x0'] + DX * i,
            p['y0'] + DY * (row - p['first_row']) + (i % 2) * DY / 2.0)


def best_scan(col, row):
    """The scan in which this hex is most completely visible."""
    best, score = None, -1
    for name, p in SCANS.items():
        cx, cy = centre(col, row, name)
        lo, hi = p['first_row'], p['last_row']
        if lo <= row <= hi:
            s = 1000
        else:
            s = -abs(row - (lo if row < lo else hi))
        if s > score:
            score, best = s, name
    return best


def neighbours(col, row):
    """Return {direction: hex_id} for the up to 6 adjacent hexes.

    Columns are offset: with i = col-1, even columns sit half a row higher than
    odd columns, so the east/west neighbours shift by one row depending on the
    parity of i.
    """
    i, j = col - 1, row - 1
    if i % 2 == 0:
        pairs = {'NE': (i + 1, j - 1), 'SE': (i + 1, j),
                 'NW': (i - 1, j - 1), 'SW': (i - 1, j)}
    else:
        pairs = {'NE': (i + 1, j), 'SE': (i + 1, j + 1),
                 'NW': (i - 1, j), 'SW': (i - 1, j + 1)}
    pairs['N'] = (i, j - 1)
    pairs['S'] = (i, j + 1)

    out = {}
    for name, (ni, nj) in pairs.items():
        ni += 1
        nj += 1
        if in_grid(ni, nj):
            out[name] = hex_id(ni, nj)
    return out



def hex_corners(col, row, scan='map1.jpg'):
    cx, cy = centre(col, row, scan)
    return [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]
