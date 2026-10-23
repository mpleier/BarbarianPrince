import os
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
        self.assertAlmostEqual(x, 80.5)
        self.assertAlmostEqual(y, 73.8, delta=0.1)

    def test_column_and_row_steps(self):
        """Column zigzag: even columns sit half a row lower than odd ones."""
        x0, y0 = centre(1, 1)
        x1, y1 = centre(2, 1)
        self.assertAlmostEqual(x1 - x0, DX)
        self.assertAlmostEqual(y1 - y0, DY / 2)
        x2, y2 = centre(3, 1)
        self.assertAlmostEqual(x2 - x0, 2 * DX)
        self.assertAlmostEqual(y2 - y0, 0)
        x3, y3 = centre(1, 2)
        self.assertAlmostEqual(y3 - y0, DY)

    def test_neighbours_are_one_row_step_apart(self):
        """Every adjacent pair of centres is exactly sqrt(3)*R apart."""
        for col in range(1, NC + 1):
            for row in range(1, NR + 1):
                cx, cy = centre(col, row)
                for n in neighbours(col, row).values():
                    nx, ny = centre(*parse_hex(n))
                    self.assertAlmostEqual(((nx - cx) ** 2 + (ny - cy) ** 2) ** 0.5,
                                           DY, delta=1e-6,
                                           msg=f'{hex_id(col, row)} -> {n}')

    def test_board_extents_match_the_printed_board(self):
        """Predicted board extents match the one-piece scan content bounds."""
        minx, miny, maxx, maxy = board_bounds()
        self.assertAlmostEqual(minx, 1.0, delta=1.0)
        self.assertAlmostEqual(miny, 5.0, delta=1.0)
        self.assertAlmostEqual(maxx, 2425.8, delta=2.0)
        self.assertAlmostEqual(maxy, 3240.9, delta=2.0)

    def test_board_fits_the_scans(self):
        """All hexes fall within the scanned image.

        The photograph is cropped inside the printed border, so the bottom
        row of the even (lower) columns runs a few pixels past the edge.
        """
        maxx, maxy = board_bounds()[2], board_bounds()[3]
        self.assertLess(maxx, 2435)
        self.assertLess(maxy, 3245)

    def test_radius_is_consistent(self):
        self.assertAlmostEqual(DX, 1.5 * R)
        self.assertAlmostEqual(DY, (3 ** 0.5) * R)

    def test_neighbour_reciprocity(self):
        for col in range(1, NC + 1):
            for row in range(1, NR + 1):
                for d, n in neighbours(col, row).items():
                    nc, nr = parse_hex(n)
                    self.assertIn(hex_id(col, row), neighbours(nc, nr).values(),
                                  msg=f'{hex_id(col, row)} -> {n} not reciprocal')


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = GameModel.load()

    def test_all_hexes_present(self):
        self.assertEqual(len(self.m.grid), 460)
        for col in range(1, NC + 1):
            for row in range(1, NR + 1):
                self.assertIn(hex_id(col, row), self.m.grid)

    def test_feature_sides_join_adjacent_hexes(self):
        """Every traced river/road side must connect two touching hexes."""
        import json
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'data', 'features.json')
        with open(path, encoding='utf-8') as f:
            feats = json.load(f)
        for kind in ('river_sides', 'road_sides'):
            for a, b in feats[kind]:
                self.assertIn(b, self.m.neighbors(a).values(),
                              msg=f'{kind}: {a}-{b} are not adjacent')

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

    def test_movement_modes_in_travel_table(self):
        """Travel table rows cover all terrains plus non-hex modes."""
        present = {r['terrain'] for r in self.m.tables['travel_table']}
        # Water hexes use 'Cross River' / 'Rafting' instead of a 'Water' row
        for t in TERRAIN_TO_TRAVEL.values():
            if t == 'Water':
                continue
            self.assertIn(t, present, msg=f'{t} missing from travel table')
        for mode in MOVEMENT_MODES:
            self.assertIn(mode, present, msg=f'{mode} missing from travel table')

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
