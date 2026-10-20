"""Unit tests for the auto-play bot (src/autoplay.py).

The engine is a prompt queue; these tests feed it hand-built prompts so the
bot's judgement can be checked without playing a whole campaign.
"""
import os
import sys
import unittest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, SRC)

from engine import Game
from autoplay import Bot, STRATEGIES


def choice(title, text, labels):
    """Build a prompt dict shaped like the engine's own prompts."""
    return {'kind': 'choice', 'title': title, 'text': text,
            'options': [{'label': l, 'handler': (lambda: 'ok')} for l in labels]}


class BotBasicsTests(unittest.TestCase):
    def test_strategies(self):
        self.assertEqual(STRATEGIES, ('cautious', 'balanced', 'aggressive'))

    def test_unknown_strategy_falls_back_to_balanced(self):
        g = Game(seed=1)
        bot = Bot(g, 'reckless')
        self.assertEqual(bot.strategy, 'balanced')

    def test_empty_prompt_returns_zero(self):
        g = Game(seed=1)
        bot = Bot(g)
        self.assertEqual(bot.choose({'title': 'x', 'text': '', 'options': []}), 0)

    def test_index_is_always_in_range(self):
        g = Game(seed=7)
        for strategy in STRATEGIES:
            bot = Bot(g, strategy)
            for n in (1, 2, 3, 5):
                p = choice('Day 1 - action in hex 0101', 'Choose.',
                           ['Travel to a new hex (r204)'] * n)
                idx = bot.choose(p)
                self.assertTrue(0 <= idx < n, f'{strategy} picked {idx} of {n}')


class SuggestTests(unittest.TestCase):
    def test_suggest_does_not_touch_memory(self):
        g = Game(seed=3)
        bot = Bot(g, 'balanced')
        menu = ('Day 1 - action in hex 0101', "Choose today's action (r203).",
                ['Travel to a new hex (r204)', 'Rest and heal wounds (r222)',
                 'Seek news & information (r209)'])
        before = (set(bot.done), dict(bot.used), list(bot.path))
        first = bot.suggest(choice(*menu))
        second = bot.suggest(choice(*menu))
        self.assertEqual(first, second)
        self.assertEqual(bot.done, before[0])
        self.assertEqual(bot.used, before[1])
        self.assertEqual(bot.path, before[2])

    def test_choose_records_memory(self):
        g = Game(seed=3)
        bot = Bot(g, 'balanced')
        menu = ('Day 1 - action in hex 0101', "Choose today's action (r203).",
                ['Travel to a new hex (r204)', 'Rest and heal wounds (r222)',
                 'Seek news & information (r209)'])
        bot.choose(choice(*menu))
        self.assertTrue(bot.done)
        self.assertTrue(bot.used)


class OfferingTests(unittest.TestCase):
    def test_offering_prefers_ten_gold(self):
        g = Game(seed=5)
        g.gold = 60
        bot = Bot(g, 'balanced')
        opts = ['Offer 1 gold', 'Offer 5 gold', 'Offer 10 gold',
                'Offer 20 gold', 'Offer 50 gold', 'Withdraw']
        idx = bot.choose(choice('Submit offerings (r212)', 'How much gold?', opts))
        self.assertEqual(opts[idx], 'Offer 10 gold')

    def test_offering_skips_unaffordable(self):
        g = Game(seed=5)
        g.gold = 7
        bot = Bot(g, 'balanced')
        opts = ['Offer 1 gold', 'Offer 5 gold', 'Offer 10 gold', 'Withdraw']
        idx = bot.choose(choice('Submit offerings (r212)', 'How much gold?', opts))
        self.assertIn('Offer', opts[idx])
        self.assertLess(int(opts[idx].split()[1]), 10)

    def test_offering_withdraws_when_broke(self):
        g = Game(seed=5)
        g.gold = 0
        bot = Bot(g, 'balanced')
        opts = ['Offer 1 gold', 'Withdraw']
        idx = bot.choose(choice('Submit offerings (r212)', 'How much gold?', opts))
        self.assertEqual(opts[idx], 'Withdraw')



MENU = ('Day 4 - action in hex 1209', "Choose today's action (r203).",
        ['Travel to a new hex (r204)', 'Rest and heal wounds (r222)',
         'Seek news & information (r209)', 'Seek to hire followers (r210)',
         'Seek an audience (r211)', 'Submit an offering (r212)'])


class ActionTests(unittest.TestCase):
    def test_temple_with_gold_offers(self):
        g = Game(seed=11)
        g.hex = '1209'                      # a temple
        g.gold = 40
        bot = Bot(g, 'balanced')
        idx = bot.choose(choice(*MENU))
        self.assertIn('offering', MENU[2][idx].lower())

    def test_omen_bonus_beats_travel(self):
        g = Game(seed=11)
        g.hex = '1209'
        g.gold = 12
        g.offering_bonus = 1
        bot = Bot(g, 'balanced')
        idx = bot.choose(choice(*MENU))
        self.assertIn('offering', MENU[2][idx].lower())

    def test_no_gold_no_offering(self):
        g = Game(seed=11)
        g.hex = '1209'
        g.gold = 3
        bot = Bot(g, 'balanced')
        idx = bot.choose(choice(*MENU))
        self.assertNotIn('offering', MENU[2][idx].lower())

    def test_wounded_party_rests(self):
        g = Game(seed=11)
        g.hex = '0101'                      # a town
        g.gold = 5
        g.prince().wounds = 4
        bot = Bot(g, 'balanced')
        idx = bot.choose(choice(*MENU))
        self.assertIn('rest', MENU[2][idx].lower())

    def test_cautious_fights_less_than_aggressive(self):
        text = 'Stand and fight (combat skill 6, endurance 5) or evade.'
        headers = ['Fight', 'Evade']
        for strategy, expect in (('cautious', 'Evade'), ('aggressive', 'Fight')):
            g = Game(seed=11)
            bot = Bot(g, strategy)
            g.pending_event = {'code': 'e050', 'headers': headers, 'rows': []}
            prompt = {'kind': 'encounter', 'title': 'e050 - Trouble', 'text': text,
                      'options': [{'label': h, 'handler': (lambda: 'ok')}
                                  for h in headers]}
            idx = bot.choose(prompt)
            self.assertEqual(headers[idx], expect,
                             f'{strategy} chose {headers[idx]}')


class MoveTests(unittest.TestCase):
    def test_prefers_road_over_swamp(self):
        g = Game(seed=2)
        g.moves_left = 2
        bot = Bot(g, 'balanced')
        # Same destination hex, so the only difference is the road bonus.
        opts = ['N -> 0102 (Countryside)', 'S -> 0102 (Countryside) [road]',
                'Stop travelling for the day']
        idx = bot.choose(choice('Move (2 hex(es) left)', 'In hex 0101.', opts))
        self.assertIn('[road]', opts[idx])

    def test_backtracking_is_penalised(self):
        g = Game(seed=2)
        g.moves_left = 1
        bot = Bot(g, 'balanced')
        bot.goal_hex = lambda: None      # isolate the ping-pong penalty
        # 0102 and 0104 are both Countryside neighbours of 0103, so the only
        # difference is that 0104 is the hex we just came from.
        bot.path = ['0104', '0103']
        opts = ['N -> 0102 (Countryside)', 'S -> 0104 (Countryside)',
                'Stop travelling for the day']
        idx = bot.choose(choice('Move (1 hex(es) left)', 'In hex 0103.', opts))
        self.assertEqual(opts[idx], 'N -> 0102 (Countryside)')

    def test_backtracks_when_it_is_the_short_way_home(self):
        g = Game(seed=2)
        g.hex = '0102'
        g.moves_left = 1
        bot = Bot(g, 'balanced')
        goal = bot.goal_hex()            # nearest temple
        # Step back to 0101 only wins if 0101 is genuinely nearer the goal.
        d = bot.distances(goal)
        if d['0101'] < d['0103']:
            bot.path = ['0101', '0102']
            opts = ['N -> 0101 (Farmland)', 'S -> 0103 (Farmland)',
                    'Stop travelling for the day']
            idx = bot.choose(choice('Move (1 hex(es) left)', 'In hex 0102.', opts))
            self.assertEqual(opts[idx], 'N -> 0101 (Farmland)')

    def test_does_not_backtrack(self):
        g = Game(seed=2)
        g.hex = '0102'
        bot = Bot(g, 'balanced')
        bot.path = ['0101', '0102']
        opts = ['N -> 0101 (Farmland)', 'S -> 0103 (Farmland)',
                'Stop travelling for the day']
        idx = bot.choose(choice('Move (1 hex(es) left)', 'In hex 0102.', opts))
        self.assertNotEqual(opts[idx], 'N -> 0101 (Farmland)')

    def test_moves_towards_the_nearest_temple(self):
        g = Game(seed=2)
        g.hex = '0101'
        g.moves_left = 1
        bot = Bot(g, 'balanced')
        goal = bot.goal_hex()
        self.assertEqual(goal, '0611')          # nearest temple from 0101
        # 0102 is one hex nearer the temple than 0201, so it should win even
        # though 0201 is unvisited and 0102 is not.
        opts = ['SE -> 0201 (Mountains)', 'S -> 0102 (Countryside)',
                'Stop travelling for the day']
        idx = bot.choose(choice('Move (1 hex(es) left)', 'In hex 0101.', opts))
        self.assertEqual(opts[idx], 'S -> 0102 (Countryside)')

    def test_stops_instead_of_wandering_away(self):
        g = Game(seed=2)
        g.hex = '0611'                          # already at the temple
        g.gold = 30
        g.moves_left = 2
        bot = Bot(g, 'balanced')
        self.assertTrue(bot.camping())
        opts = ['N -> 0610 (Wasteland)', 'S -> 0612 (Wasteland)',
                'Stop travelling for the day']
        idx = bot.choose(choice('Move (2 hex(es) left)', 'In hex 0611.', opts))
        self.assertEqual(opts[idx], 'Stop travelling for the day')

    def test_stop_travelling_when_no_moves_left(self):
        g = Game(seed=2)
        g.moves_left = 0
        bot = Bot(g, 'balanced')
        opts = ['N -> 0102 (Farmland)', 'Stop travelling for the day']
        idx = bot.choose(choice('Move (0 hex(es) left)', 'In hex 0101.', opts))
        self.assertEqual(opts[idx], 'Stop travelling for the day')


class ResourceTests(unittest.TestCase):
    def test_food_prefers_stores(self):
        g = Game(seed=4)
        g.food = 5
        bot = Bot(g, 'balanced')
        opts = ['Buy meals (1 gold)', 'Eat from stores (1 units)', 'Go hungry (r216)']
        idx = bot.choose(choice('Evening meal - need 1 food units', 'Party needs 1.', opts))
        self.assertIn('eat from stores', opts[idx].lower())

    def test_lodging_paid_when_affordable(self):
        g = Game(seed=4)
        g.gold = 50
        bot = Bot(g, 'balanced')
        opts = ['Pay 2 gold for lodging', 'Sleep rough (risk desertion)']
        idx = bot.choose(choice('Lodging in town 0101 (r217)', '2 room(s) = 2 gold.', opts))
        self.assertEqual(idx, 0)

    def test_lodging_skipped_when_broke(self):
        g = Game(seed=4)
        g.gold = 1
        bot = Bot(g, 'balanced')
        opts = ['Pay 2 gold for lodging', 'Sleep rough (risk desertion)']
        idx = bot.choose(choice('Lodging in town 0101 (r217)', '2 room(s) = 2 gold.', opts))
        self.assertEqual(idx, 1)


class CampaignTests(unittest.TestCase):
    """The bot must survive the engine without raising, whatever the seed."""

    def test_campaigns_complete(self):
        for strategy in STRATEGIES:
            for seed in (1, 2, 3, 42):
                g = Game(seed=seed)
                bot = Bot(g, strategy)
                g.run_until_idle(max_steps=6000, chooser=bot.choose)
                self.assertTrue(g.game_over, f'{strategy}/seed {seed} did not finish')
                self.assertTrue(g.day >= 1)
                self.assertTrue(g.gold >= 0)

    def test_naive_chooser_also_survives(self):
        g = Game(seed=42)
        g.run_until_idle(max_steps=6000)
        self.assertTrue(g.game_over)

    def test_goal_hex_is_a_real_hex(self):
        g = Game(seed=42)
        bot = Bot(g, 'balanced')
        goal = bot.goal_hex()
        self.assertIsNotNone(goal)
        self.assertIn(goal, g.model.grid)


if __name__ == '__main__':
    unittest.main()
