# Rewrite test_model.py for single-scan geometry
content = r'''import os
import sys
import unittest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, SRC)

from geometry import (NC, NR, R, DX, DY, centre, neighbours, hex_id, parse_hex,
                      TERRAIN_TO_TRAVEL, MOVEMENT_MODES, board_xy, board_corners,
                      board_bounds)
from game_model import GameModel


class GeometryTests(unittest.TestCase):
    def test_grid_size(self):
        self.assertEqual(NC * NR, 460)

    def test_hex_id_roundtrip(self):
        for col, row in [(1, 1), (20, 23), (7, 12)]:
            self.assertEqual(parse_hex(hex_id(col, row)), (col, row))

    def test_first_hex_centre(self):
        x, y = centre(1, 1)
        self.assertAlmostEqual(x, 111.0)
        self.assertAlmostEqual(y, 78.1, delta=0.1)

    def test_column_and_row_steps(self):
        x0, y0 = centre(1, 1)
        x1, y1 = centre(2, 1)
        self.assertAlmostEqual(x1 - x0, DX)
        self.assertAlmostEqual(y1 - y0, DY / 2)
        x2, y2 = centre(1, 2)
        self.assertAlmostEqual(y2 - y0, DY)

    def test_board_is_continuous(self):
        for col in range(1, NC + 1):
            bottom = board_xy(col, 12)[1] + DY / 2
            top = board_xy(col, 13)[1] - DY / 2
            self.assertAlmostEqual(bottom, top, delta=1e-6,
                                   msg=f'column {col} does not meet at row 12/13')

    def test_board_extents_match_the_printed_board(self):
        minx, miny, maxx, maxy = board_bounds()
        self.assertAlmostEqual(minx, 30.0, delta=1.0)
        self.assertAlmostEqual(miny, 8.0, delta=1.0)
        self.assertAlmostEqual(maxx, 2500.5, delta=2.0)
        self.assertAlmostEqual(maxy, 3305.0, delta=10.0)

    def test_board_fits_the_scans(self):
        maxx, maxy = board_bounds()[2], board_bounds()[3]
        self.assertLess(maxx, 2720)
        self.assertLess(maxy, 3300)

    def test_radius_is_consistent(self):
        self.assertAlmostEqual(DX, 1.5 * R)
        self.assertAlmostEqual(DY, (3 ** 0.5) * R)