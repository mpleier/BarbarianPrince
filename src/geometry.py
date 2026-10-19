"""Unified hex-grid + rules model for the BarbarianPrince board.

Geometry (measured directly from the white grid lines in both board scans;
the full measurement is reproduced by `python _refs/verify_seam.py`, whose
output is saved in _refs/verify_seam_out.txt, and cross-checked by
_refs/edge_extremes.py and _refs/flat_edges.py):
  * flat-top hexes, 20 columns x 23 rows = 460 hexes
  * hex id = CCRR  (column 01-20, row 01-23)
  * hex radius R = 106.0 px in the scans
  * column step DX = 1.5 * R, row step DY = sqrt(3) * R
  * odd columns are shifted down by DY/2
  * map1.jpg holds rows 01-12, map2.jpg holds rows 13-23

Anchor points measured from the scans (flat horizontal hex edges are R px
long and are centred on the column axis, so an edge at y = cy +/- sqrt(3)R/2
pins the row, and its x-extent pins the column):

  map1.jpg  row1/row2 boundary  y = 190.5   -> row 1 centre y = 98.2
            column 1 flat edge  x = 324..430 -> column 1 centre x = 377.0
            row11/row12 boundary y = 2027.5
  map2.jpg  row12/row13 boundary y = 111.5  -> row 13 centre y = 203.3
            column 1 flat edge  x = 324..430 -> column 1 centre x = 377.0

Least-squares fits of the printed grid lines give
  map1: row pitch 183.55 px (R = 105.97), max residual 1.7 px
  map2: row pitch 184.16 px (R = 106.33), max residual 7.0 px
map2 is very slightly stretched relative to map1, so the lattice is anchored
on the shared 12/13 grid line; the residual drift grows to ~7 px by row 23,
which is scan distortion rather than a lattice error.  R = 106.0 is the best
single compromise.  The column pitch is pinned by the board's right edge: the
printed board ends at x ~ 3504, which is exactly column 20's right vertex for
DX = 1.5 * 106.0, and the flat hex edges on the row boundaries sit on the
predicted column axes to within ~2.5 px.

Resulting board extents in the stitched (map1) pixel frame:
  x 271.0 .. 3504.0   (the right vertex is directly measurable - the scan's
                       coloured content ends at x = 3509, i.e. the printed edge
                       sits on column 20's right vertex; the left vertex is
                       inferred, because the white paper margin blends with the
                       white hex fills)
  y   6.4 .. 4320.9   (the lattice's top edge is at y = 6.4 but is hidden under
                       the scan's grey border band, y ~ 0-17; the scan is
                       cropped at unified y ~ 4241, so the bottom row's zigzag
                       overhangs the paper)
The stitch seam sits at SEAM_Y = 2209.57, against a printed 12/13 line measured
at 2209.5 - a 0.07 px error.
"""
import math

SQ3 = math.sqrt(3.0)
R = 106.0
DX = 1.5 * R
DY = SQ3 * R
NC, NR = 20, 23

# (x0, y0) of the centre of column 1 at row `first_row`, per scan.
#
# Fitted by least-squares on the printed grid lines (_refs/verify_seam.py):
#   map1: row pitch 183.55 px (R = 105.97), max residual 1.7 px
#   map2: row pitch 184.16 px (R = 106.33), max residual 7.0 px
# R = 106.0 is the best single value.  Origins are anchored on the shared
# 12/13 grid line so the two scans meet exactly at the seam.
SCANS = {
    'map1.jpg': {'x0': 377.0, 'y0': 98.2, 'first_row': 1, 'last_row': 12},
    'map2.jpg': {'x0': 377.0, 'y0': 203.3, 'first_row': 13, 'last_row': 23},
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


# The board is photographed in two halves (map1 = rows 1-12, map2 = rows 13-23).
# `centre()` is scan-local; BOARD_Y_OFF puts map2 into map1's pixel frame so the
# whole 20x23 board can be drawn/stitched in one coordinate system.
#
# The offset is derived from the lattice so that the row 12 / row 13 boundary is
# a single continuous line across the seam:
#     map1 bottom edge = y0_1 + 12*DY - DY/2
#     map2 top edge    = y0_2 + offset
BOARD_Y_OFF = {
    'map1.jpg': 0.0,
    'map2.jpg': (SCANS['map1.jpg']['y0'] + DY * (SCANS['map2.jpg']['first_row'] - 1)
                 - SCANS['map2.jpg']['y0']),
}

# Unified y of the row 12 / row 13 boundary - the stitch line between the scans.
SEAM_Y = SCANS['map1.jpg']['y0'] + DY * (NR - 11) - DY / 2.0


def board_xy(col, row):
    """Unified pixel position of a hex on the stitched board."""
    scan = best_scan(col, row)
    x, y = centre(col, row, scan)
    return (x, y + BOARD_Y_OFF[scan])


def board_corners(col, row):
    cx, cy = board_xy(col, row)
    return [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]


def board_bounds():
    """(minx, miny, maxx, maxy) of the whole 20x23 board in unified pixels."""
    xs, ys = [], []
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            for x, y in board_corners(col, row):
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys))

