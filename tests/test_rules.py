"""Rule-by-rule conformance tests (r201-r228).

Each test asserts one clause of the booklet that the engine claims to model,
with the rule number in the docstring.  Unlike ``test_events`` (which drives the
event data) these tests pin the *mechanics*: costs, dice, modifiers, thresholds
and the order of effects, so a regression in a rule shows up as a named failure.
"""
import os
import sys
import unittest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, SRC)

from engine import Game, Character, Combat, RAFT_SPEED  # noqa: E402
from game_model import GameModel  # noqa: E402


def game(**kw):
    g = Game(seed=kw.pop('seed', 7))
    g.start()
    for key, value in kw.items():
        setattr(g, key, value)
    return g


class CharacterTests(unittest.TestCase):
    """r201-r202 - the Prince's starting statistics and purse."""

    def test_prince_starts_with_skill_8_endurance_9(self):
        g = game()
        p = g.prince()
        self.assertEqual((p.skill, p.endurance), (8, 9))
        self.assertEqual(p.wealth, 2)

    def test_wit_is_one_die_and_a_one_counts_as_two(self):
        # r202: wit is rolled during __init__, so the die is patched on the
        # class before the game is created.
        original = Game.d1
        try:
            Game.d1 = lambda self: 1
            self.assertEqual(Game(seed=3).wit, 2)
        finally:
            Game.d1 = original
        for seed in range(1, 12):
            wit = Game(seed=seed).wit
            self.assertTrue(2 <= wit <= 6)

    def test_starting_gold_comes_from_the_wealth_2_treasure_row(self):
        # r202 -> r225/r226: wealth code 2, one die on the Treasure Table
        # (the row reads 0, 1, 2, 2, 3, 4).
        original = Game.d1
        try:
            Game.d1 = lambda self: 6
            self.assertEqual(Game(seed=4).gold, 4)
            Game.d1 = lambda self: 1
            self.assertEqual(Game(seed=4).gold, 0)
        finally:
            Game.d1 = original


class DailyActionTests(unittest.TestCase):
    """r203 - only the actions legal in the hex are offered."""

    def labels(self, g):
        g.daily_menu()
        prompt = g.current()
        return [o['label'].lower() for o in prompt['options']]

    def test_wilderness_has_no_news_hire_audience_or_ruins(self):
        g = game(hex='0405')                     # countryside, no place
        labels = ' | '.join(self.labels(g))
        for banned in ('news', 'hire', 'audience', 'offering', 'ruins'):
            self.assertNotIn(banned, labels)

    def test_temple_offers_news_audience_and_offering(self):
        g = game(hex='0611')                     # Branwyn's Temple
        labels = ' | '.join(self.labels(g))
        for wanted in ('news', 'audience', 'offering'):
            self.assertIn(wanted, labels)

    def test_ruins_offers_the_search(self):
        g = game(hex='0307')                     # Dead Plains Ruins
        self.assertIn('ruins', ' | '.join(self.labels(g)))


class TravelTests(unittest.TestCase):
    """r204-r205 - speeds, roads and getting lost."""

    def test_speed_on_foot_mounted_and_winged(self):
        g = game()
        self.assertEqual(g.speed(), 1)           # anyone on foot slows the party
        g.prince().mount = 'horse'
        self.assertEqual(g.speed(), 2)           # everyone mounted
        g.prince().mount = 'winged'
        self.assertEqual(g.speed(), 3)           # everyone flying

    def test_guide_subtracts_one_from_the_lost_roll(self):
        g = game(hex='0303')
        g.d2 = lambda: 8                         # forest threshold is 8+
        self.assertTrue(g.check_lost('Forest'))  # 8 >= 8 without a guide
        g.party.append(Character('Guide', 3, 4, guide=True))
        g.d2 = lambda: 8                         # 8 - 1 = 7 < 8
        self.assertFalse(g.check_lost('Forest'))
        g.d2 = lambda: 9                         # 9 - 1 = 8 >= 8
        self.assertTrue(g.check_lost('Forest'))

    def test_no_lost_check_on_a_road(self):
        g = game()
        roads = [tuple(p) for p in g.road_sides]
        self.assertTrue(roads, 'the traced road sides are empty')
        a, b = roads[0]
        g.hex = a
        g.moves_left = 1
        self.assertTrue(g.is_road_move(a, b))
        g.d2 = lambda: 12                        # would be lost on any terrain
        self.assertTrue(g.move(b))
        self.assertFalse(any('Getting lost' in line for line in g.log))


class TransportTests(unittest.TestCase):
    """r206 - load weights and carrying capacity."""

    def test_load_weights(self):
        g = game()
        g.gold = 150
        g.food = 3
        # r206a: 3 food + ceil(150/100) = 5 loads
        self.assertEqual(g.current_loads(), 5)
        g.gold = 100
        self.assertEqual(g.current_loads(), 4)   # exactly one load for 100

    def test_capacity_of_a_man_and_a_mount(self):
        self.assertEqual(Character('Man', 3, 4).load_capacity(), 10)
        g = game()
        self.assertEqual(g.max_capacity(), 10)   # one man on foot
        g.prince().mount = 'horse'
        # r206b: a mount carries 30, but the rider counts as 20 of them
        self.assertEqual(g.max_capacity(), 10)


class RuinsTests(unittest.TestCase):
    """r208 - two dice, straight on the ruins table."""

    def test_roll_maps_straight_to_the_table(self):
        g = game(hex='0307')
        g.d2 = lambda: 4
        g.search_ruins()
        self.assertTrue(any('e136' in line for line in g.log))

    def test_no_bonus_for_strong_followers(self):
        g = game(hex='0307')
        g.party.append(Character('Hero', 7, 8))
        g.d2 = lambda: 2
        g.search_ruins()
        self.assertTrue(any('rolled 2' in line for line in g.log))


class NewsTests(unittest.TestCase):
    """r209 - two dice, +1 for 5 gold, +1 for wit 5+."""

    def test_bonuses_and_cost(self):
        g = game(hex='0601', gold=10)
        g.wit = 5
        g.d2 = lambda: 2
        g.seek_news()
        self.assertEqual(g.gold, 5)               # 5 gold spent
        self.assertTrue(any('rolled 4 (bonus 2)' in line for line in g.log))

    def test_no_spend_when_broke(self):
        g = game(hex='0601', gold=0)
        g.d2 = lambda: 2
        g.seek_news()
        self.assertEqual(g.gold, 0)


class AudienceTests(unittest.TestCase):
    """r211 - the temple modifiers depend on the party's calling."""

    def test_monk_adds_one_and_magician_subtracts_two(self):
        g = game(hex='0611')
        g.d2 = lambda: 5
        g.party.append(Character('Warrior Monk', 5, 6))
        g.seek_audience()
        self.assertTrue(any('+1' in line and 'modifier' in line for line in g.log))

        g2 = game(hex='0611')
        g2.d2 = lambda: 5
        g2.party.append(Character('Magician', 4, 5))
        g2.seek_audience()
        self.assertTrue(any('-2' in line for line in g2.log))


class OfferingTests(unittest.TestCase):
    """r212 - 14+ wins the Staff; 10 gold buys +1."""

    def test_ten_gold_with_the_omen_reaches_fourteen(self):
        g = game(hex='0611', gold=50, offering_bonus=1)
        g.d2 = lambda: 12                        # 12 + 1 (gold) + 1 (omen) = 14
        g.offering(10)
        self.assertTrue(g.staff)

    def test_ten_gold_alone_caps_at_thirteen(self):
        g = game(hex='0611', gold=50)
        g.d2 = lambda: 12                        # 12 + 1 = 13 < 14
        g.offering(10)
        self.assertFalse(g.staff)

    def test_plain_roll_cannot_reach_fourteen(self):
        g = game(hex='0611', gold=50)
        g.d2 = lambda: 12                        # 12 + 0 = 12 < 14
        g.offering(1)
        self.assertFalse(g.staff)

    def test_arrest_confiscates_the_purse(self):
        g = game(hex='0611', gold=50)
        g.d2 = lambda: 4                         # 4 + 1 = 5 -> arrested
        g.offering(10)
        self.assertEqual(g.gold, 0)


class RaftTests(unittest.TestCase):
    """r213 - raft travel follows river hexsides, three a day."""

    def test_raft_offers_only_river_sides_and_three_moves(self):
        g = game(hex='0102')
        self.assertTrue(g.raft_available())
        g.begin_action('raft')
        self.assertTrue(g.raft)
        self.assertEqual(g.moves_left, RAFT_SPEED)
        prompt = g.current()
        self.assertTrue(all('[river]' in o['label'] or 'stop' in o['label'].lower()
                            for o in prompt['options']))

    def test_a_twelve_stops_the_raft(self):
        g = game(hex='0101')
        g.begin_action('raft')
        g.d2 = lambda: 4
        self.move_to(g, '0102')
        g.moves_left = 1                         # last hexside of the day
        g.d2 = lambda: 12
        self.move_to(g, '[river]')
        self.assertFalse(g.raft)

    def test_other_rolls_keep_the_raft(self):
        g = game(hex='0102')
        g.begin_action('raft')
        g.moves_left = 1
        g.d2 = lambda: 10
        self.move_to(g, '[river]')
        self.assertTrue(g.raft)

    def move_to(self, g, needle):
        """Answer the current move prompt, choosing `needle` in the label."""
        prompt = g.current() or (g.advance() and g.current())
        index = next(i for i, o in enumerate(prompt['options'])
                     if needle in o['label'])
        g.answer(index)

    def test_downriver_day_allows_three_hexsides(self):
        # r213: the water runs top to bottom, so 0101 -> 0102 is downstream.
        g = game(hex='0101')
        g.begin_action('raft')
        g.d2 = lambda: 4
        self.move_to(g, '0102')
        self.assertEqual(g.raft_dir, 'down')
        self.assertEqual(g.moves_left, 2)        # three moves minus this one

    def test_upriver_day_allows_only_two_hexsides(self):
        g = game(hex='0102')
        g.begin_action('raft')
        g.d2 = lambda: 4
        self.move_to(g, '0101')
        self.assertEqual(g.raft_dir, 'up')
        self.assertEqual(g.moves_left, 1)        # two moves minus this one

    def test_every_river_side_has_a_flow_direction(self):
        # features.json carries "a|b" -> downstream for every traced side.
        g = game()
        self.assertTrue(g.river_flow)
        for pair in g.river_sides:
            a, b = sorted(pair)
            self.assertIn(f'{a}|{b}', g.river_flow)
            self.assertIn(g.river_flow[f'{a}|{b}'], (a, b))


class CacheTests(unittest.TestCase):
    """r214 - the recovery die: 1-4 intact, 5 lost track, 6 looted."""

    def test_found_intact(self):
        g = game(hex='0405', gold=120)
        g.cache(120)
        g.d1 = lambda: 3
        g.recover_cache()
        self.assertEqual(g.gold, 120)
        self.assertNotIn('0405', g.caches)

    def test_not_found_keeps_the_cache(self):
        g = game(hex='0405', gold=120)
        g.cache(120)
        g.d1 = lambda: 5
        g.recover_cache()
        self.assertEqual(g.gold, 0)
        self.assertIn('0405', g.caches)

    def test_looted_removes_the_cache(self):
        g = game(hex='0405', gold=120)
        g.cache(120)
        g.d1 = lambda: 6
        g.recover_cache()
        self.assertEqual(g.gold, 0)
        self.assertNotIn('0405', g.caches)


class HuntingTests(unittest.TestCase):
    """r215b - skill + half endurance - 2 dice, plus rest-day helpers."""

    def test_base_hunt_total(self):
        g = game(hex='0405')                     # countryside
        g.party = [Character('Cal Arath (the Prince)', 8, 9, prince=True)]
        g.d2 = lambda: 5
        g.hunt(1)
        # 8 + 4 - 5 = 7 units
        self.assertEqual(g.food, 7)

    def test_rest_day_lets_the_party_join(self):
        g = game(hex='0405')
        g.party.append(Character('Friend', 3, 4))
        g.action = 'rest'
        g.d2 = lambda: 5
        g.hunt(1)
        # 8 + 4 - 5 = 7, plus one extra hunter = 8
        self.assertEqual(g.food, 8)


class FarmlandHuntTests(unittest.TestCase):
    """r215c - hunting in farmland: 1-4 nothing, 5 e017, 6 e050 at +2."""

    def hunt_with_event_die(self, hexid, die, visited=None):
        g = game(hex=hexid)
        if visited:
            g.visited |= visited
        g.d1 = lambda: die
        g.hunt(1)
        return g

    def test_peasant_mob_on_a_five(self):
        g = self.hunt_with_event_die('0102', 5)
        self.assertEqual((g.pending_event or {}).get('code'), 'e017')

    def test_constabulary_on_a_six_adds_two_to_the_die(self):
        # 0108 is farmland within one hex of Angleae (0109), so e050 applies.
        g = self.hunt_with_event_die('0108', 6)
        self.assertEqual((g.pending_event or {}).get('code'), 'e050')
        self.assertEqual(g.pending_event['bonus'], 2)
        self.assertTrue(any('add two (+2)' in line for line in g.log))

    def test_constabulary_is_ignored_far_from_civilisation(self):
        g = self.hunt_with_event_die('2011', 6)   # 7 hexes from any place
        self.assertIsNone(g.pending_event)

    def test_ogon_and_weshor_send_e002_instead(self):
        g = self.hunt_with_event_die('0102', 6, visited={'0101'})
        self.assertEqual((g.pending_event or {}).get('code'), 'e002')

    def test_no_event_die_outside_farmland(self):
        g = self.hunt_with_event_die('0405', 6)   # countryside
        self.assertIsNone(g.pending_event)

    def test_four_or_less_is_quiet(self):
        g = self.hunt_with_event_die('0108', 4)
        self.assertIsNone(g.pending_event)


class ConstabularyTests(unittest.TestCase):
    """e050 - the option matrix and its visited/never-visited modifiers."""

    def test_matrix_has_three_columns_and_eight_rows(self):
        from engine import parse_options
        model = GameModel.load()
        headers, rows, note = parse_options(model.events['e050']['text'])
        self.assertEqual([h.lower() for h in headers],
                         ['negotiate', 'evade', 'fight'])
        self.assertEqual([roll for roll, _ in rows], list(range(1, 9)))
        self.assertEqual(rows[4][1][1], ('hide', 'r318'))
        self.assertIn('mounts', note.lower())

    def option_bonus(self, visited, escaped=()):
        g = game(hex='0108')
        g.visited |= set(visited)
        g.escaped_from |= set(escaped)
        g.encounter('e050')
        return g.pending_event, g.option_bonus(g.pending_event)

    def test_visited_place_gives_plus_two(self):
        prompt, bonus = self.option_bonus({'0109'})
        self.assertEqual(prompt['code'], 'e050')
        self.assertEqual(bonus, 2)

    def test_never_visited_gives_plus_one(self):
        _prompt, bonus = self.option_bonus(set())
        self.assertEqual(bonus, 1)

    def test_escaping_from_the_place_cancels_the_bonus(self):
        _prompt, bonus = self.option_bonus({'0109'}, {'0109'})
        self.assertEqual(bonus, 0)


class StarvationTests(unittest.TestCase):
    """r216 - the Prince starves too, but never deserts."""

    def test_prince_goes_hungry(self):
        g = game(hex='0405')
        g.starve(2)
        p = g.prince()
        self.assertEqual(p.starved, 1)
        self.assertEqual(p.effective_skill, 7)
        self.assertEqual(p.load_capacity(), 5)

    def test_followers_may_desert(self):
        g = game(hex='0405')
        g.party.append(Character('Follower', 3, 4))
        g.wit = 2
        g.d2 = lambda: 12                        # 12 - 2 = 10 >= 4
        g.starve(1)
        self.assertEqual(len(g.living()), 1)


class LodgingTests(unittest.TestCase):
    """r217 - rooms, stables and the cost of sleeping rough."""

    def test_room_and_stable_costs(self):
        g = game(hex='1109')                     # Cawther, a town
        g.party = [Character('Cal Arath (the Prince)', 8, 9, prince=True,
                             mount='horse')]
        g.lodging()
        prompt = g.current()
        self.assertIn('2 gold', prompt['text'])  # 1 room + 1 stable

    def test_prince_does_not_desert_but_his_mount_can_be_stolen(self):
        g = game(hex='1109')
        p = g.prince()
        p.mount = 'horse'
        g.d1 = lambda: 4
        g.sleep_rough()
        self.assertTrue(p.alive)
        self.assertEqual(p.mount, 'none')


class FixedDice:
    """Stand-in RNG that always rolls the same total on two dice."""

    def __init__(self, total):
        self.total = total

    def randint(self, low, high):
        return self.total // 2


class CombatTests(unittest.TestCase):
    """r220-r221 - strike resolution, wound modifiers and helplessness."""

    def test_strike_total_is_skill_difference_plus_two_dice(self):
        striker = Character('Striker', 8, 9)
        target = Character('Target', 6, 6)
        combat = Combat([striker], [target], FixedDice(10))   # 8 - 6 + 10 = 12
        wounds = combat.strike(striker, target)
        self.assertEqual(wounds, GameModel.load().combat_wounds(12))

    def test_wounded_target_is_easier_to_hit_and_wounded_striker_worse(self):
        striker = Character('Striker', 6, 6)
        target = Character('Target', 6, 6)
        combat = Combat([striker], [target], FixedDice(7))
        self.assertEqual(combat.modifiers(striker, target), 0)
        target.wounds = 3                       # half of 6: seriously wounded
        self.assertEqual(combat.modifiers(striker, target), 2)
        striker.wounds = 1
        self.assertEqual(combat.modifiers(striker, target), 1)   # +2 -1
        striker.wounds = 3                      # half of 6: -1 more
        self.assertEqual(combat.modifiers(striker, target), 0)  # +2 -1 -1

    def test_wound_thresholds(self):
        c = Character('Man', 4, 8)
        c.wounds = 3
        self.assertFalse(c.serious)
        c.wounds = 4
        self.assertTrue(c.serious)              # r221a: half endurance
        c.wounds = 7
        self.assertTrue(c.unconscious)          # r221b: one short of death
        self.assertEqual(c.effective_skill, 0)  # helpless
        c.wounds = 8
        self.assertTrue(c.dead)                 # r221c


class RestTests(unittest.TestCase):
    """r222 - rest heals a wound, but never a poison wound."""

    def test_rest_heals_one_wound(self):
        g = game(hex='0604')
        p = g.prince()
        p.wounds = 3
        g.d2 = lambda: 2                         # no travel event
        g.rest()
        self.assertEqual(p.wounds, 2)

    def test_poison_wounds_never_heal(self):
        g = game(hex='0604')
        p = g.prince()
        p.wounds = 3
        p.poisoned = 2
        g.d2 = lambda: 2
        g.rest()
        self.assertEqual(p.wounds, 2)            # heals the ordinary wound only
        g.rest()
        self.assertEqual(p.wounds, 2)            # nothing left to heal


class AuditTests(unittest.TestCase):
    """The audit document must cover every rule the model carries."""

    def test_every_rule_is_in_the_audit(self):
        import json
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'data', 'rules.json'), encoding='utf-8') as f:
            rules = json.load(f)
        with open(os.path.join(root, '_audit', 'RULES.md'), encoding='utf-8') as f:
            audit = f.read()
        missing = [rid for rid in rules if rid not in audit
                   and not (rid.startswith('r3') and 'r300-r343' in audit)]
        self.assertEqual(missing, [], f'rules missing from _audit/RULES.md: {missing}')


if __name__ == '__main__':
    unittest.main()
