"""Unified hex-grid model for the BarbarianPrince board.

Geometry calibrated from a single one-piece scan
(_refs/BPMap.jpg, 2435x3235):
  * flat-top hexes, 20 columns x 23 rows = 460 hexes
  * hex id = CCRR  (column 01-20, row 01-23)
  * hex radius R = 79.5 px in the scans
  * column step DX = 1.5 * R, row step DY = sqrt(3) * R
  * even columns sit half a row lower than odd columns (column zigzag)
  * SCAN_Y0 positioned so row 1 centre aligns near the top of image content

Scan layout: the one-piece scan content starts at approximately x=1, y=5.
The hex grid is anchored to this content frame.

Calibration note: the one-piece scan has a slightly different aspect ratio
(~0.75) than the theoretical hex grid (~0.77), due to perspective distortion
in the photograph.  R was chosen to keep all hex corners within the image
bounds.

Board extents in the scan pixel frame:
  x    1.0 .. 2425.8   (left vertex of column 1 near x = 1;
                        right vertex of column 20 near x = 2426)
  y    5.0 .. 3240.9   (top edge of row 1 in the odd columns near y = 5;
                        row 23 in the even columns runs ~6 px past the
                        bottom border of the photograph)

The column zigzag is visible on the scan: the printed hex numbers sit half a
row lower in every even column, and the traced roads only close up as hex
sides under this parity.
"""
import math

SQ3 = math.sqrt(3.0)
R = 79.5
DX = 1.5 * R
DY = SQ3 * R
NC, NR = 20, 23

# Anchor: centre of column 1, row 1 in scan pixel coordinates.
SCAN_X0 = 80.5
SCAN_Y0 = 73.8490


def _column_offset(col):
    """Vertical offset of a column's hex centres, in scan pixels.

    Even columns sit half a row lower than odd ones, so every adjacent pair
    of columns is half a hex out of step.
    """
    return DY / 2 if col % 2 == 0 else 0.0


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
            SCAN_Y0 + DY * (row - 1) + _column_offset(col))


def neighbours(col, row):
    """Return {direction: hex_id} for the up to 6 adjacent hexes.

    Even columns sit half a row lower than odd ones, so the east/west
    neighbours of an odd column are one row *above* those of the even column
    beside it, and vice versa: the row offsets depend on column parity.
    """
    if col % 2 == 1:                      # odd column: even neighbours sit lower
        pairs = {'NE': (col + 1, row - 1), 'SE': (col + 1, row),
                 'NW': (col - 1, row - 1), 'SW': (col - 1, row)}
    else:                                 # even column: odd neighbours sit higher
        pairs = {'NE': (col + 1, row), 'SE': (col + 1, row + 1),
                 'NW': (col - 1, row), 'SW': (col - 1, row + 1)}
    pairs['N'] = (col, row - 1)
    pairs['S'] = (col, row + 1)

    return {name: hex_id(nc, nr) for name, (nc, nr) in pairs.items()
            if in_grid(nc, nr)}


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
