"""Unified hex-grid model for the BarbarianPrince board.

Geometry calibrated from a single one-piece scan
(_refs/barbarianprince_onepiecemap-revc.jpg):
  * flat-top hexes, 20 columns x 23 rows = 460 hexes
  * hex id = CCRR  (column 01-20, row 01-23)
  * hex radius R = 79.5 px in the scans
  * column step DX = 1.5 * R, row step DY = sqrt(3) * R
  * even columns are aligned with top, odd columns shifted down by DY/2
  * SCAN_Y0 shifted upward to align hex row 1 centers near top of image

Scan margins: the one-piece scan has a sidebar on the left (~220px wide)
containing the map key. The hex grid content starts after the sidebar.
SCAN_X0 is anchored to the center of hex 0101 (Ogon) which accounts for
the sidebar offset.

Calibration note: the one-piece scan has a different aspect ratio (~0.83)
than the theoretical hex grid (~0.77), due to perspective distortion in
the photograph.  R was chosen to fit the vertical extent (23 rows), so
there is some horizontal margin.

Board extents in the scan pixel frame:
  x  220.5 .. 2645.2   (left vertex of column 1 near x = 220;
                        right vertex of column 20 near x = 2645)
  y   10.6 .. 3246.5   (top vertex of row 1 near y = 11;
                       bottom row near y ~ 3247)

Calibrated by _refs/recalibrate_geometry.py.
"""
import math

SQ3 = math.sqrt(3.0)
R = 79.5
DX = 1.5 * R
DY = SQ3 * R
NC, NR = 20, 23

# Anchor: centre of column 1, row 1 in scan pixel coordinates.
# Adjusted for the sidebar offset in the one-piece scan.
# Shifted down by DY/2 for correct hex center alignment.
SCAN_X0 = 300.0
SCAN_Y0 = 79.4462

# Map legend terrain -> terrain name used by the Travel Table (r207).
TERRAIN_TO_TRAVEL = {
    'farmland': 'Farmland',
    'countryside': 'Countryside',
    'forest': 'Forest',
    'hills': 'Hills',
    'badlands': 'Hills',        # treated as hills for travel purposes
    'desert': 'Desert',
    'swamp': 'Swamp',
    'mountain': 'Mountains',
    'mountains': 'Mountains',    # hex data uses plural
    'water': 'Water',
}

MOVEMENT_MODES = ('Cross River', 'On Road', 'Airborne', 'Rafting')


def hex_id(col, row):
    return f'{col:02d}{row:02d}'


def parse_hex(hid):
    return int(hid[:2]), int(hid[2:])


def in_grid(col, row):
    return 1 <= col <= NC and 1 <= row <= NR


def centre(col, row):
    """Pixel centre of a hex in the single scan."""
    i = col - 1
    return (SCAN_X0 + DX * i,
            SCAN_Y0 + DY * (row - 1) + (col % 2) * DY / 2.0)


def neighbours(col, row):
    """Return {direction: hex_id} for the up to 6 adjacent hexes.

    Columns are offset: even columns sit half a row higher than odd columns,
    so the east/west neighbours shift by one row depending on the parity
    of the column index.
    """
    i, j = col - 1, row - 1
    if col % 2 == 0:
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


def hex_corners(col, row):
    cx, cy = centre(col, row)
    return [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]


# Single scan, so board_xy and centre are the same.
board_xy = centre


def board_corners(col, row):
    cx, cy = board_xy(col, row)
    return [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]


def board_bounds():
    """(minx, miny, maxx, maxy) of the whole 20x23 board in scan pixels."""
    xs, ys = [], []
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            for x, y in board_corners(col, row):
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys))
