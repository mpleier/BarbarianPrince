"""Tests for the victory and defeat conditions (src/engine.py).

Victory (r212 result 14+): the Staff of Command is won, and the Prince must
carry it to a hex north of the Tragoth River.  Defeat includes the arrest
events e060-e063, where the Prince is jailed and may be executed by the
headsman (e061).
"""
import os
import sys
import unittest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, SRC)

from engine import Game, Character  # noqa: E402
from game_model import GameModel  # noqa: E402


class NorthOfTragothTests(unittest.TestCase):
    """The 20 north-bank hexes and the north_of_tragoth() helper."""

    NORTH = {'0101', '0201', '0301', '0302', '0501', '0502', '0601', '0701',
             '0801', '0901', '1001', '1101', '1201', '1301', '1501', '1601',
             '1701', '1801', '1901', '2001'}

    def setUp(self):
        self.model = GameModel.load()

    def test_north_hexes_match_the_booklet(self):
        self.assertEqual(Game.NORTH_OF_TRAGOTH, frozenset(self.NORTH))

    def test_north_of_tragoth_helper(self):
        game = Game(model=self.model, seed=1)
        for h in self.NORTH:
            self.assertTrue(game.north_of_tragoth(h), h)
        # a few known south-bank hexes
        for h in ('0102', '0113', '0420', '0611', '1212', '2018'):
            self.assertFalse(game.north_of_tragoth(h), h)

    def test_north_of_tragoth_defaults_to_current_hex(self):
        game = Game(model=self.model, seed=1)
        game.hex = '0101'
        self.assertTrue(game.north_of_tragoth())
        game.hex = '0102'
        self.assertFalse(game.north_of_tragoth())


class VictoryTests(unittest.TestCase):
    """Winning needs the Staff AND being north of the Tragoth."""

    def setUp(self):
        self.model = GameModel.load()

    def test_staff_and_north_wins(self):
        game = Game(model=self.model, seed=1)
        game.start()
        game.staff = True
        game.hex = '0101'          # Ogon, north of the river
        game.day = 10
        game.finish_day()
        self.assertTrue(game.game_over)
        self.assertTrue(game.won)
        self.assertIn('north of the Tragoth', game.reason)

    def test_staff_but_south_does_not_win(self):
        game = Game(model=self.model, seed=1)
        game.start()
        game.staff = True
        game.hex = '0102'          # south bank of the river
        game.day = 10
        game.finish_day()
        self.assertFalse(game.game_over)
        self.assertFalse(game.won)
        self.assertTrue(any('carry it north' in line
                            for line in game.log if isinstance(line, str)))

    def test_no_staff_but_north_does_not_win(self):
        game = Game(model=self.model, seed=1)
        game.start()
        game.staff = False
        game.hex = '0101'
        game.day = 10
        game.finish_day()
        self.assertFalse(game.game_over)
        self.assertFalse(game.won)

    def test_win_day_count_still_loses_after_70(self):
        game = Game(model=self.model, seed=1)
        game.start()
        game.staff = False
        game.hex = '0101'
        game.day = 70
        game.finish_day()
        self.assertTrue(game.game_over)
        self.assertFalse(game.won)
        self.assertIn('Ten weeks', game.reason)

    def test_offering_14_grants_staff_and_two_warrior_monks(self):
        game = Game(model=self.model, seed=1)
        game.start()
        game.gold = 100
        game.offering_bonus = 2
        game.d2 = lambda: 12       # 12 + 2 bonus = 14 -> Staff of Command
        game.offering(10)
        self.assertTrue(game.staff)
        monks = [c for c in game.party if 'Monk' in c.name]
        self.assertEqual(len(monks), 2)
        self.assertTrue(all(c.skill == 5 and c.endurance == 6
                            and c.mount == 'horse' for c in monks))


class ArrestDefeatTests(unittest.TestCase):
    """e060-e063: the Prince is arrested, jailed and may be executed."""

    def setUp(self):
        self.model = GameModel.load()

    def _arrest(self, seed=1):
        game = Game(model=self.model, seed=seed)
        game.start()
        game.gold = 40
        game.party.append(Character('Squire', 4, 5, mount='horse'))
        game.items.append('Special possession A')
        game.encounter('e061')
        return game

    def test_e061_arrest_confiscates_and_imprisons(self):
        game = self._arrest()
        self.assertEqual(game.imprisoned, 'e061')
        self.assertEqual(game.gold, 0)
        self.assertEqual(game.items, [])
        for c in game.living():
            self.assertEqual(c.mount, 'none')
        self.assertFalse(game.game_over)

    def test_e061_headsman_executes_the_prince(self):
        game = self._arrest()
        game.d1 = lambda: 6        # the headsman's die
        game.prison_step()
        self.assertTrue(game.game_over)
        self.assertFalse(game.won)
        self.assertIn('executed', game.reason)

    def test_e061_escape_frees_the_prince(self):
        game = self._arrest()
        game.d1 = lambda: 1        # escape die
        game.prison_step()
        self.assertIsNone(game.imprisoned)
        self.assertFalse(game.game_over)
        self.assertTrue(any('free again' in line
                            for line in game.log if isinstance(line, str)))

    def test_e060_roll_5_6_is_a_minor_offence_fine(self):
        game = Game(model=self.model, seed=1)
        game.start()
        game.gold = 50
        game.d1 = lambda: 5        # minor offence branch
        cost = 10 + 2 * len(game.living())
        game._minor_offence()
        self.assertIsNone(game.imprisoned)
        self.assertEqual(game.gold, 50 - cost)

    def test_e060_roll_1_sentences_to_death_prison(self):
        game = Game(model=self.model, seed=1)
        game.start()
        game.gold = 50
        game.d1 = lambda: 1        # gravity roll -> e061
        game.encounter('e060')
        self.assertEqual(game.imprisoned, 'e061')
        self.assertEqual(game.gold, 0)

    def test_prison_run_until_idle_reaches_day_70_defeat(self):
        game = self._arrest()
        game.d1 = lambda: 3        # never escape, never executed
        game.d2 = lambda: 7
        game.run_until_idle(max_steps=300)
        self.assertTrue(game.game_over)
        self.assertFalse(game.won)
        self.assertIn('prison', game.reason.lower())


if __name__ == '__main__':
    unittest.main()