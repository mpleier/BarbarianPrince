"""Unified hex-grid model for the BarbarianPrince board.

Geometry calibrated from a single one-piece scan
(_refs/BPMap.jpg, 2435x3235):
  * flat-top hexes, 20 columns x 23 rows = 460 hexes
  * hex id = CCRR  (column 01-20, row 01-23)
  * hex circumradius RX = 79.1 px horizontally, RY = 80.4 px vertically
  * column step DX = 1.5 * RX, row step DY = sqrt(3) * RY
  * even columns sit half a row lower than odd columns (column zigzag)
  * SCAN_Y0 positioned so row 1 centre aligns with the top of the artwork

The photograph is a little taller than the board's true proportions, so the
printed grid is not perfectly regular.  Fitting the drawn borders as an
anisotropic lattice (RX != RY) instead of a regular one drops the mean
distance from a lattice edge to the nearest printed border from 7.5 px to
5.8 px, which is what makes the overlay line up across the whole board.

Board extents in the scan pixel frame:
  x    4.3 .. 2416.9   (left vertex of column 1, right vertex of column 20)
  y   -5.8 .. 3290.3   (the scan is cropped inside the printed border, so the
                        top of row 1 and the bottom of row 23 are cut off)

The column zigzag is visible on the scan: the printed hex numbers sit half a
row lower in every even column, and the traced roads only close up as hex
sides under this parity.
"""
import math

SQ3 = math.sqrt(3.0)

RX = 79.1                      # horizontal circumradius
RY = 80.4                      # vertical circumradius
R = RX                         # historical alias: the horizontal radius
DX = 1.5 * RX                  # column step
DY = SQ3 * RY                  # row step
NC, NR = 20, 23

# Anchor: centre of column 1, row 1 in scan pixel coordinates.
SCAN_X0 = 83.4
SCAN_Y0 = 74.65


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
    return [(cx + RX * math.cos(math.radians(a)),
             cy + RY * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]


# Single scan, so board_xy and centre are the same.
board_xy = centre


def board_corners(col, row):
    cx, cy = board_xy(col, row)
    return [(cx + RX * math.cos(math.radians(a)),
             cy + RY * math.sin(math.radians(a)))
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
