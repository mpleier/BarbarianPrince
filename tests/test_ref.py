"""The booklet reference window (web `/api/ref`) and its option tables.

The booklet prints each event's option matrix inside the entry's prose
("... die roll Negotiate * evade fight 1 surprised r308 ..."), so a reference
window that dumps the raw text shows an unreadable run-on paragraph.  The API
splits the prose from the matrix and the page draws the matrix as a table.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from engine import OPTION_VERBS, parse_options  # noqa: E402


class ReferencePayloadTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import web
        cls.web = web

    def test_e050_shows_prose_then_a_table(self):
        r = self.web.api_ref('e050')
        self.assertEqual(r['id'], 'e050')
        self.assertEqual(r['title'], 'Local Constabulary')
        # the matrix is pulled out of the prose
        self.assertNotIn('Negotiate', r['text'])
        self.assertNotIn('surprised r308', r['text'])
        self.assertTrue(r['text'].rstrip().endswith('the die roll.'))

        opts = r['options']
        self.assertEqual([h.lower() for h in opts['headers']],
                         ['negotiate', 'evade', 'fight'])
        self.assertEqual(opts['rolls'], list(range(1, 9)))
        self.assertEqual(len(opts['rows']), 8)
        self.assertEqual(opts['rows'][4][1], {'label': 'hide', 'ref': 'r318'})
        self.assertIn('mounts', opts['note'])

    def test_rules_carry_no_option_table(self):
        r = self.web.api_ref('r213')
        self.assertIsNone(r['options'])
        self.assertIn('raft', r['title'].lower())

    def test_every_matrix_event_round_trips(self):
        """Each event whose text has a matrix must return one from the API."""
        events = self.web.MODEL.events
        for code, ev in sorted(events.items()):
            parsed = parse_options(ev['text'])
            if not parsed:
                continue
            r = self.web.api_ref(code)
            self.assertIsNotNone(r['options'], msg=f'{code} lost its table')
            self.assertEqual(len(r['options']['rows']), len(parsed[1]),
                             msg=f'{code} row count')
            self.assertEqual(len(r['options']['headers']), len(parsed[0]),
                             msg=f'{code} column count')
            # the prose keeps the words ("(talk, evade, fight)") but the
            # run-on header row must be gone
            self.assertNotIn(' '.join(parsed[0][:2]), r['text'],
                             msg=f'{code} still shows the matrix in the prose')
            self.assertLess(len(r['text']), len(ev['text']), msg=code)


class OptionDataTests(unittest.TestCase):
    """data/event_options.json is generated from the parser; keep it honest."""

    def setUp(self):
        with open(os.path.join(ROOT, 'data', 'event_options.json'),
                  encoding='utf-8') as f:
            self.options = json.load(f)
        with open(os.path.join(ROOT, 'data', 'events.json'),
                  encoding='utf-8') as f:
            self.events = json.load(f)

    def test_tables_have_sane_shape(self):
        for code, table in self.options.items():
            cols = table['columns']
            self.assertTrue(2 <= len(cols) <= 6, msg=f'{code}: {len(cols)} columns')
            self.assertTrue(cols and any(c.strip().lower() in OPTION_VERBS
                                         for c in cols),
                            msg=f'{code}: no option verb among {cols}')
            self.assertGreaterEqual(len(table['rows']), 2, msg=code)
            for row in table['rows']:
                self.assertEqual(len(row['cells']), len(cols),
                                 msg=f'{code} roll {row["roll"]}')

    def test_tables_match_the_printed_text(self):
        for code, table in self.options.items():
            parsed = parse_options(self.events[code]['text'])
            self.assertIsNotNone(parsed, msg=f'{code} no longer parses')
            headers, rows, _note = parsed
            self.assertEqual([h.strip('*') for h in headers], table['columns'],
                             msg=f'{code} columns')
            self.assertEqual([roll for roll, _cells in rows],
                             [row['roll'] for row in table['rows']],
                             msg=f'{code} rolls')


if __name__ == '__main__':
    unittest.main()
