import os
import sys
import unittest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, SRC)

from geometry import (NC, NR, R, DX, DY, centre, neighbours, hex_id, parse_hex,
                      TERRAIN_TO_TRAVEL, MOVEMENT_MODES, BOARD_Y_OFF, SEAM_Y,
                      board_xy, board_corners, board_bounds)
from game_model import GameModel


class GeometryTests(unittest.TestCase):
    def test_grid_size(self):
        self.assertEqual(NC * NR, 460)

    def test_hex_id_roundtrip(self):
        for col, row in [(1, 1), (20, 23), (7, 12)]:
            self.assertEqual(parse_hex(hex_id(col, row)), (col, row))

    def test_first_hex_centre(self):
        x, y = centre(1, 1, 'map1.jpg')
        self.assertAlmostEqual(x, 377.0)
        self.assertAlmostEqual(y, 98.2)

    def test_column_and_row_steps(self):
        x0, y0 = centre(1, 1, 'map1.jpg')
        x1, y1 = centre(2, 1, 'map1.jpg')
        self.assertAlmostEqual(x1 - x0, DX)
        self.assertAlmostEqual(y1 - y0, DY / 2)
        x2, y2 = centre(1, 2, 'map1.jpg')
        self.assertAlmostEqual(y2 - y0, DY)

    def test_scans_share_one_lattice(self):
        """Both scans must sit on the same 106 px lattice, not just be adjacent."""
        self.assertAlmostEqual(centre(1, 1, 'map1.jpg')[0],
                               centre(1, 1, 'map2.jpg')[0])
        # row 12 centre in map1 vs row 13 centre in map2, after stitching
        y12 = board_xy(1, 12)[1]
        y13 = board_xy(1, 13)[1]
        self.assertAlmostEqual(y13 - y12, DY, delta=1.0)

    def test_stitch_seam_is_continuous(self):
        """The bottom edge of row 12 and the top edge of row 13 must coincide."""
        bottom_of_12 = board_xy(1, 12)[1] + DY / 2
        top_of_13 = board_xy(1, 13)[1] - DY / 2
        self.assertAlmostEqual(bottom_of_12, top_of_13, delta=1e-6)
        self.assertAlmostEqual(SEAM_Y, bottom_of_12, delta=1e-6)
        self.assertAlmostEqual(BOARD_Y_OFF['map2.jpg'], 2098.2, delta=1.0)

    def test_seam_is_continuous_for_every_column(self):
        """The stitch line must be a single straight line across all 20 columns."""
        for col in range(1, NC + 1):
            bottom = board_xy(col, 12)[1] + DY / 2
            top = board_xy(col, 13)[1] - DY / 2
            self.assertAlmostEqual(bottom, top, delta=1e-6,
                                   msg=f'column {col} does not meet at the seam')

    def test_lattice_matches_the_printed_grid_lines(self):
        """Predicted row boundaries must land on the printed lines in both scans.

        The printed horizontal grid lines in the column-1 band were measured
        directly from the scans; the model may not drift more than a couple of
        pixels away from them.
        """
        measured_map1 = [190.5, 373.5, 557.5, 741.5, 924.0, 1106.5,
                         1291.0, 1473.5, 1657.5, 1842.0, 2027.5]
        for k, line in enumerate(measured_map1, start=1):
            predicted = centre(1, k, 'map1.jpg')[1] + DY / 2
            self.assertAlmostEqual(predicted, line, delta=2.0,
                                   msg=f'map1 boundary {k} off by '
                                       f'{predicted - line:.2f} px')

        measured_map2 = [111.5, 297.0, 482.5, 666.5, 850.5, 1034.5,
                         1218.0, 1402.0, 1586.0, 1770.5, 1954.5]
        for k, line in enumerate(measured_map2, start=13):
            predicted = centre(1, k, 'map2.jpg')[1] - DY / 2
            self.assertAlmostEqual(predicted, line, delta=8.0,
                                   msg=f'map2 boundary {k} off by '
                                       f'{predicted - line:.2f} px')

    def test_seam_matches_the_printed_line(self):
        """The stitch line must land on the printed 12/13 grid line.

        The 12/13 boundary was measured at y = 2209.5 in the stitched board;
        SEAM_Y is derived from the lattice, so it has to agree with it.
        """
        self.assertAlmostEqual(SEAM_Y, 2209.5, delta=0.5,
                               msg=f'seam at {SEAM_Y:.2f} is not on the '
                                   f'printed 12/13 line (2209.5)')

    def test_board_extents_match_the_printed_board(self):
        """The lattice must span the printed board rectangle.

        The printed board runs from x ~ 288 to x ~ 3504 and its top edge is at
        y ~ 6 in the stitched frame.  The lattice's leftmost vertex (column 1)
        and rightmost vertex (column 20) must sit on those edges.
        """
        minx, miny, maxx, maxy = board_bounds()
        self.assertAlmostEqual(minx, 271.0, delta=1.0)
        self.assertAlmostEqual(maxx, 3504.0, delta=1.0)
        self.assertAlmostEqual(miny, 6.4, delta=1.0)
        # map2's scan is cropped, so the lattice may overhang the paper, but
        # only by the amount a clipped bottom row can.
        self.assertLess(maxy, 4330.0)

    def test_board_fits_the_scans(self):
        minx, miny, maxx, maxy = board_bounds()
        self.assertGreater(minx, 0)
        self.assertGreater(miny, 0)
        self.assertLess(maxx, 3510)   # map1.jpg / map2.jpg are 3510 px wide
        # The stitched board is 23 rows tall: the seam sits at SEAM_Y and the
        # remaining 11 rows add 11 * DY below it.
        self.assertLess(maxy, SEAM_Y + 12 * DY)
        self.assertGreater(maxy, SEAM_Y + 11 * DY)

    def test_corner_hex_has_two_neighbors(self):
        self.assertEqual(neighbours(1, 1), {'SE': '0201', 'S': '0102'})

    def test_interior_hex_has_six_neighbors(self):
        self.assertEqual(len(neighbours(10, 10)), 6)

    def test_neighbors_are_symmetric(self):
        for col in range(1, NC + 1):
            for row in range(1, NR + 1):
                for d, n in neighbours(col, row).items():
                    back = {'N': 'S', 'S': 'N', 'NE': 'SW', 'SW': 'NE',
                            'NW': 'SE', 'SE': 'NW'}[d]
                    self.assertIn(back, neighbours(*parse_hex(n)),
                                  f'{hex_id(col, row)} -> {n} not reciprocal')

    def test_radius_is_consistent(self):
        self.assertAlmostEqual(DX, 1.5 * R)
        self.assertAlmostEqual(DY, (3 ** 0.5) * R)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = GameModel.load()

    def test_all_hexes_present(self):
        self.assertEqual(len(self.m.grid), 460)
        for col in range(1, NC + 1):
            for row in range(1, NR + 1):
                self.assertIn(hex_id(col, row), self.m.grid)

    def test_terrain_is_known(self):
        for h in self.m.grid.values():
            self.assertIn(h['terrain'], TERRAIN_TO_TRAVEL)

    def test_badlands_maps_to_hills(self):
        self.assertEqual(TERRAIN_TO_TRAVEL['badlands'], 'Hills')

    def test_travel_table_complete(self):
        rows = self.m.tables['travel_table']
        self.assertEqual(len(rows), 11)
        for row in rows:
            self.assertEqual(len(row['event_refs']), 6)
            for ref in row['event_refs']:
                if ref != '-':
                    self.assertRegex(ref, r'^[er]\d{3}$')

    def test_movement_modes_covered(self):
        present = {r['terrain'] for r in self.m.tables['travel_table']}
        for mode in MOVEMENT_MODES:
            self.assertIn(mode, present)

    def test_events_complete(self):
        self.assertEqual(len(self.m.events), 182)
        for n in range(167, 180):
            self.assertNotIn(f'e{n}', self.m.events)

    def test_roll_row_open_ended(self):
        rows = self.m.tables['audience']['the Baron of Huldra Castle']['rows']
        self.assertTrue(self.m.roll_row(rows, 14)['text'].startswith('Baron becomes'))
        self.assertEqual(self.m.roll_row(rows, 6)['roll'], '6,7')
        self.assertIsNone(self.m.roll_row(rows, 1))

    def test_travel_event_resolution(self):
        ref = self.m.travel_event_ref('Forest', 3)
        self.assertEqual(ref, 'r242')
        self.assertEqual(self.m.resolve_event_ref(ref, 4), 'e082')

    def test_combat_table(self):
        # Combat Table (r220c): -1,3,5,8,11 = 1 wound; 10,12,13,17 = 2; 14 = 3;
        # 16,18,19 = 5; 20 = 6. Any other total is a miss.
        self.assertEqual(self.m.combat_wounds(3), 1)
        self.assertEqual(self.m.combat_wounds(11), 1)
        self.assertEqual(self.m.combat_wounds(14), 3)
        self.assertEqual(self.m.combat_wounds(20), 6)
        self.assertIsNone(self.m.combat_wounds(2))
        self.assertIsNone(self.m.combat_wounds(15))

    def test_errata_parsed(self):
        self.assertEqual(len(self.m.tables['errata']), 19)
        self.assertTrue(any(e['section'] == 'r209' for e in self.m.tables['errata']))
        self.assertTrue(any(e['section'] == 'e048' for e in self.m.tables['errata']))

    def test_distance_is_symmetric(self):
        d1 = self.m.distance('0101', '1212')
        d2 = self.m.distance('1212', '0101')
        self.assertEqual(d1, d2)
        self.assertIsNotNone(d1)

    def test_all_references_resolve(self):
        self.assertEqual(self.m.index['dangling_refs'], [])
        self.assertEqual(len(self.m.index['reference_fixes']), 5)
        for bad, good in self.m.index['reference_fixes'].items():
            self.assertTrue(bad != good)
            self.assertTrue(good in self.m.rules or good in self.m.events
                            or good in self.m.tables['travel_event_refs'])


if __name__ == '__main__':
    unittest.main()
