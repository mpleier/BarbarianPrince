"""Tests for the encounter/event system (src/engine.py).

Every event in the booklet model must reach the player with its full set of
options and resolve without raising an exception or looping forever.
"""
import os
import sys
import unittest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, SRC)

from engine import Game, parse_options, die_entries, Character  # noqa: E402
from game_model import GameModel  # noqa: E402
from autoplay import Bot  # noqa: E402

KNOWN_REFS = set('r%03d' % n for n in range(300, 344))


class OptionMatrixTests(unittest.TestCase):
    """The 'die roll / talk / evade / fight' tables as the booklet writes them."""

    def test_e002_keeps_all_three_columns_and_the_footnote_row(self):
        model = GameModel.load()
        headers, rows, note = parse_options(model.events['e002']['text'])
        self.assertEqual(headers, ['negotiate', 'evade', 'fight'])
        self.assertEqual([roll for roll, _ in rows], [1, 2, 3, 4, 5, 6, 7])
        cells = rows[3][1]
        self.assertEqual(cells[0], ('bribe to pass (15)', 'r323'))
        self.assertEqual(cells[1], ('hide', 'r318'))
        # roll 7 is a footnote row: only the footnoted evade column has an entry
        self.assertEqual(rows[6][1][1], ('escape mtd', 'r312'))
        self.assertIsNone(rows[6][1][0][1])
        self.assertIn('mounted', note.lower())

    def test_e130_audience_cell_has_no_reference(self):
        model = GameModel.load()
        headers, rows, _ = parse_options(model.events['e130']['text'])
        self.assertEqual(headers, ['talk', 'evade', 'fight'])
        self.assertEqual(rows[3][1][0], ('audience', None))
        self.assertEqual(rows[3][1][1], ('hide', 'r317'))
        self.assertEqual(rows[2][1][0], ('arrested', 'e060'))

    def test_e021_roll_again_cell(self):
        model = GameModel.load()
        headers, rows, _ = parse_options(model.events['e021']['text'])
        self.assertEqual(headers, ['talk', 'evade', 'fight'])
        self.assertEqual(rows[5][1][0], ('roll again', None))
        self.assertEqual(rows[5][1][1], ('pass', 'r329'))

    def test_e100_misprinted_reference_is_normalised(self):
        model = GameModel.load()
        headers, rows, _ = parse_options(model.events['e100']['text'])
        self.assertEqual(headers, ['talk', 'evade', 'fight'])
        self.assertEqual(rows[5][1], [('surprised', 'r309'),
                                      ('attacked', 'r306'),
                                      ('surprised', 'r308')])

    def test_e005_headers_are_not_swallowed_by_the_stat_block(self):
        model = GameModel.load()
        headers, rows, _ = parse_options(model.events['e005']['text'])
        self.assertEqual(headers, ['talk', 'evade', 'fight'])
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[3][1][1], ('hide', 'r119'))


    def test_die_table_supports_shared_rolls(self):
        entries = die_entries('Roll one die: 1-nothing; 2-e150; 5,6-e152')
        self.assertEqual(entries, [([1], 'nothing'), ([2], 'e150'),
                                   ([5, 6], 'e152')])

    def test_every_option_reference_is_known(self):
        model = GameModel.load()
        fixes = model.index.get('reference_fixes', {})
        for code, ev in sorted(model.events.items()):
            parsed = parse_options(ev['text'])
            if not parsed:
                continue
            for roll, cells in parsed[1]:
                for label, ref in cells:
                    if ref is None:
                        continue
                    ref = fixes.get(ref, ref)
                    if ref.startswith('e'):
                        self.assertIn(ref, model.events,
                                     f'{code} roll {roll} -> {ref} missing')
                    else:
                        self.assertIn(ref, KNOWN_REFS,
                                     f'{code} roll {roll} -> {ref} unknown')


class EncounterResolutionTests(unittest.TestCase):
    """Drive every event through the engine and make sure it terminates."""

    @classmethod
    def setUpClass(cls):
        cls.model = GameModel.load()

    def resolve(self, code, strategy='balanced'):
        game = Game(model=self.model, seed=20261020)
        game.start()
        game.encounter(code)
        bot = Bot(game, strategy)
        steps = 0
        while game.is_busy() and steps < 300:
            prompt = game.current()
            if not prompt.get('options'):
                self.fail(f'{code}: prompt "{prompt["title"]}" has no options')
            game.answer(bot.choose(prompt))
            steps += 1
        self.assertLess(steps, 300, f'{code} never resolved')
        return game

    def test_all_events_resolve(self):
        for code in sorted(self.model.events):
            self.resolve(code)

    def test_events_with_options_offer_every_column(self):
        for code, ev in sorted(self.model.events.items()):
            parsed = parse_options(ev['text'])
            if not parsed:
                continue
            headers = parsed[0]
            game = Game(model=self.model, seed=1)
            game.start()
            game.encounter(code)
            prompt = game.current()
            self.assertEqual(len(prompt['options']), len(headers),
                             f'{code}: {len(prompt["options"])} options for '
                             f'{len(headers)} columns')

    def test_bribe_option_is_paid_from_the_cell_label(self):
        game = Game(model=self.model, seed=3)
        game.start()
        game.gold = 20
        game.encounter('e002')
        game.pending_event['rows'] = [(4, [('bribe to pass (15)', 'r323'),
                                           ('hide', 'r318'),
                                           ('attack', 'r304')])]
        game.d1 = lambda: 4
        game.roll_option(0)
        self.assertEqual(game.gold, 5)

    def test_lord_audience_is_resolved_from_the_footnote(self):
        game = Game(model=self.model, seed=5)
        game.start()
        game.encounter('e130')
        outcome = game.lord_audience(game.pending_event)
        self.assertTrue(outcome)
        self.assertTrue(any('Audience' in n for n in game.log))

    def test_e007_matrix_has_eight_rows(self):
        headers, rows, note = parse_options(self.model.events['e007']['text'])
        self.assertEqual(headers, ['talk', 'evade', 'fight'])
        self.assertEqual([roll for roll, _ in rows], list(range(1, 9)))
        self.assertIn('forest', note.lower())

    def test_forest_bonus_shifts_the_die_roll(self):
        game = Game(model=self.model, seed=7)
        game.start()
        game.hex = '0202'                      # a forest hex
        self.assertEqual(game.model.terrain('0202'), 'forest')
        game.encounter('e007')
        game.d1 = lambda: 6
        game.roll_option(0)                    # 6 + 2 = 8 -> 'pass' r329
        self.assertTrue(any('die 6 + 2 = 8: pass' in line
                            for line in game.log if isinstance(line, str)))

    def test_e112_follow_option_chains_to_another_event(self):
        headers, rows, _ = parse_options(self.model.events['e112']['text'])
        self.assertEqual(headers, ['evade', 'follow', 'fight'])
        self.assertEqual(rows[0][1][1], ('ambush', 'e113'))
        game = Game(model=self.model, seed=9)
        game.start()
        game.encounter('e112')
        game.d1 = lambda: 1
        game.roll_option(1)
        self.assertTrue(any(p.get('code') == 'e113' for p in game.prompts))

    def test_mounted_escape_replaces_the_evade_roll(self):
        game = Game(model=self.model, seed=11)
        game.start()
        game.party.append(Character('Squire', 4, 5, mount='horse'))
        game.encounter('e005')
        override = game.evade_override(game.pending_event, 'evade')
        self.assertEqual(override, 'r312')
        self.assertIsNone(game.evade_override(game.pending_event, 'talk'))
        footless = Game(model=self.model, seed=12)
        footless.start()
        footless.encounter('e005')
        self.assertIsNone(footless.evade_override(footless.pending_event, 'evade'))

    def test_roll_again_rerolls_and_terminates(self):
        game = Game(model=self.model, seed=17)
        game.start()
        game.encounter('e021')
        game.d1 = lambda: 6
        game.roll_option(0)                    # row 6 talk = 'roll again'
        self.assertEqual(game.pending_event.get('rerolls'), 3)
        self.assertTrue(any('encounter ends' in line
                            for line in game.log if isinstance(line, str)))

    def test_re_encounter_attempts_are_capped(self):
        game = Game(model=self.model, seed=13)
        game.start()
        game.encounter('e004')
        game.d1 = lambda: 1
        attempts = []
        for _ in range(6):
            game.re_encounter()
            if game.pending_event:
                attempts.append(game.pending_event['attempts'])
        self.assertLessEqual(max(attempts), 3)
        self.assertIsNone(game.pending_event)
        self.assertTrue(any('it ends' in line
                            for line in game.log if isinstance(line, str)))


class DailyMenuTests(unittest.TestCase):
    """r213 - the raft option is only offered where the river is reachable."""

    def setUp(self):
        self.model = GameModel.load()

    def menu_labels(self, game):
        game.daily_menu()
        return [o['label'] for o in game.current()['options']]

    def test_raft_is_not_offered_inland(self):
        game = Game(model=self.model, seed=21)
        game.hex = '0320'                      # inland farmland, no river hexside
        self.assertFalse(game.raft_available())
        labels = self.menu_labels(game)
        self.assertFalse(any('raft' in label.lower() for label in labels))

    def test_raft_is_offered_next_to_a_river(self):
        game = Game(model=self.model, seed=22)
        game.hex = '0102'                      # touches the Tragoth river
        self.assertTrue(game.raft_available())
        labels = self.menu_labels(game)
        self.assertTrue(any('raft' in label.lower() for label in labels))

    def test_raft_stays_available_while_afloat(self):
        game = Game(model=self.model, seed=23)
        game.raft = True
        game.hex = '0320'
        self.assertTrue(game.raft_available())
        self.assertTrue(any('raft' in label.lower() for label in self.menu_labels(game)))
        game.begin_action('rest')              # any other action gets you off
        self.assertFalse(game.raft)
        self.assertFalse(game.raft_available())

    def test_raft_action_refuses_a_hex_with_no_river(self):
        game = Game(model=self.model, seed=24)
        game.hex = '0320'
        self.assertEqual(game.begin_action('raft'), 'No raft available.')
        self.assertFalse(game.raft)

    def test_rolling_12_ends_the_raft_trip(self):
        """r213 - after a day on the raft, a stop check of 12 ends the trip and
        dismantles the raft (the move-based design replaces the old dice table)."""
        game = Game(model=self.model, seed=25)
        game.raft = True                   # the party is already afloat
        game.hex = '0102'
        game.d2 = lambda: 12
        game.raft_stop_check()
        self.assertFalse(game.raft)
        self.assertTrue(any('stopping point' in line
                            for line in game.log if isinstance(line, str)))


if __name__ == '__main__':
    unittest.main()
