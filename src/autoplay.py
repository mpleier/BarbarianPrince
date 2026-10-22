"""Rule-aware auto-play for the Barbarian Prince engine.

The engine is a queue of prompts; this module supplies the judgement.  A ``Bot``
scores every option of the prompt currently on the queue and answers with the
best one, so a whole 70-day campaign can be played headlessly - or watched step
by step in the web front-end.

Three personalities are available:

  cautious    avoids fights, keeps a gold buffer, rests when hurt
  balanced    the default: sensible travel, opportunistic fighting
  aggressive  seeks battle, hires big parties, spends gold freely

The win condition is the Staff of Command (r212, offerings at a temple), so the
bot steers towards temples once it has gold to spare.
"""
import heapq
import re
from collections import deque

from engine import parse_foes
import camp_dp
from camp_dp import camp_action, camp_value

STRATEGIES = ('cautious', 'balanced', 'aggressive')

# r212: the Staff of Command needs a 14+ offering roll.  2d12 tops out at 12,
# so the roll needs modifiers: +1 for a 10-gold sacrifice, +1 for the omen won
# by seeking news (r209) or by a previous offering (r212 result 7), and +3 for
# the High Priest's influence (r212 result 12/13).  Everything the bot does
# before that is in service of those numbers.
GOLD_GOAL = 10
TOTAL_DAYS = 70

# Economics measured over 300 campaigns (_refs/day_yield.py, _refs/camp_policy_sim.py):
#   a day spent searching a ruins hex nets ~ +5.9 gold
#   a temple day costs the offering only: r216 starvation and r217 rough
#   sleeping roll for *follower* desertion, so an unaccompanied Prince eats
#   and sleeps for free and every gold goes into the r212 roll.
RUIN_YIELD = 5.9
CAMP_OVERHEAD = 3       # upkeep a party with followers must pay at a temple
CAMP_COST = 1           # cheapest possible temple day for a lone Prince
GOLD_CEILING = 400          # a camp can never spend more than this
MIN_CAMP_DAYS = 5           # temple days still worth travelling for
# _refs/macro_dp5.py runs the exact camp DP against the real ruins lottery
# (97.3% nothing, 1.7% 60 gold, 1.1% 500 gold) and solves the ruin phase as a
# stopping problem: mining costs nothing, and camping with no gold is worthless,
# so the party should keep digging until the gold target is reached or the camp
# would be too short to be worth it.  _refs/ratio_sweep.py confirms it on the
# engine: 0.56 -> 0.167 wins, 1.0 -> 0.225.  The time budget is therefore only a
# safety net; the real limit is `ruins_cap`.
RUIN_RATIO = 1.0

# r205 "getting lost": 2d6 against the terrain of the hex you are *leaving*.
# Roads are exempt, so a road step always costs exactly one day, while a swamp
# step costs 1 / (1 - 15/36) = 1.42 days on average.  Routing on expected days
# rather than hex counts is worth several days a campaign.
LOST_THRESHOLD = {'Farmland': 10, 'Countryside': 9, 'Forest': 8, 'Hills': 8,
                  'Mountains': 7, 'Swamp': 5, 'Desert': 6, 'Cross River': 8,
                  'On Road': None, 'Airborne': 12, 'Rafting': None}


def _p_lost(terrain):
    """P(2d6 >= threshold) for the r205 getting-lost check."""
    thr = LOST_THRESHOLD.get(terrain)
    if thr is None:
        return 0.0
    return sum(1 for a in range(1, 7) for b in range(1, 7) if a + b >= thr) / 36


HEX_RE = re.compile(r'->\s*(\d{4})')
NEED_RE = re.compile(r'need\s+(\d+)')
GOLD_RE = re.compile(r'(\d+)\s*gold')
PAY_RE = re.compile(r'for\s+(\d+)\s*gold/day')
COUNT_RE = re.compile(r'Hire all (\d+)')
BUY_RE = re.compile(r'Buy (\d+) horse')
WEALTH_RE = re.compile(r'wealth\s+(\d+)')

# Travel Table (r207) terrain -> how pleasant / safe the hex is.
TERRAIN_SCORE = {'Farmland': 3, 'Countryside': 3, 'Forest': 2, 'Hills': 2,
                 'Mountains': -4, 'Swamp': -4, 'Desert': -6}
PLACE_SCORE = {'town': 4, 'castle': 4, 'temple': 6, 'ruins': 2,
               'camp': 1, 'pass': 1, 'marsh': -2}
TERRAIN_RISK = {'Mountains': 4, 'Desert': 5, 'Swamp': 3, 'Forest': 2,
                'Wasteland': 2, 'Farmland': 0, 'Countryside': 0, 'River': 1}

# r210 horse dealer: the hire roll is 2d6 (+1 in a hex already learned from
# r209) and a dealer appears on a 5 or a 10, i.e. 7/36 of the time.
DEALER_ODDS = 7 / 36.0

# Personality weights: everything the bot cares about, in one table.
PROFILE = {
    'cautious':   dict(travel=9,  rest=12, news=6, hire=5,  audience=2,
                       ruins=3,  raft=4,  fight=-3, flee=7,  talk=6, caution=2,
                       buffer=30, min_party=2, max_party=4),
    'balanced':   dict(travel=10, rest=8,  news=7, hire=8,  audience=6,
                       ruins=8,  raft=5,  fight=2,  flee=4,  talk=4, caution=1,
                       buffer=20, min_party=3, max_party=6),
    'aggressive': dict(travel=12, rest=6,  news=7, hire=11, audience=9,
                       ruins=12, raft=6,  fight=6,  flee=1,  talk=2, caution=0,
                       buffer=10, min_party=4, max_party=8),
}

# (action name, substring of the daily-menu label)
ACTION_KEYS = (('travel', 'travel'), ('rest', 'rest'), ('news', 'news'),
               ('hire', 'hire'), ('audience', 'audience'),
               ('offering', 'offering'), ('ruins', 'ruins'),
               ('cache', 'cache'), ('raft', 'raft'))



def _alive(chars):
    return [c for c in chars if getattr(c, 'alive', True) and not c.dead]


def _power(chars):
    """Rough combat rating: skill drives hits, endurance drives survival."""
    return sum(c.effective_skill * 2 + max(0, c.endurance - c.wounds)
               for c in _alive(chars))


class Bot:
    """Pick the best option of the engine's current prompt."""

    def __init__(self, game, strategy='balanced'):
        self.game = game
        self.strategy = strategy if strategy in STRATEGIES else 'balanced'
        # risk: negative = risk-averse, positive = risk-hungry
        self.p = PROFILE[self.strategy]
        self.path = [game.hex]
        self.tried = set()
        self.done = set()          # (hex, action) already attempted
        self.used = {}             # (hex, action) -> times attempted
        self.ruin_days = 0         # days spent searching ruins this campaign
        self._dist = {}
        self._travel = {}

    # ------------------------------------------------------------ helpers
    def party(self):
        return self.game.living()

    def my_power(self):
        return _power(self.party())

    def distances(self, start):
        """BFS over the hex graph, cached per starting hex."""
        d = self._dist.get(start)
        if d is not None:
            return d
        d = {start: 0}
        q = deque([start])
        while q:
            h = q.popleft()
            for nb in self.game.model.neighbors(h).values():
                if nb not in d:
                    d[nb] = d[h] + 1
                    q.append(nb)
        self._dist[start] = d
        return d

    def travel_days(self, target):
        """Expected number of travel days from every hex to `target`.

        BFS counts hexes, but r205 makes a day of travel vanish with probability
        ``p_lost`` of the terrain you are *leaving*, so a step costs
        ``1 / (1 - p_lost)`` days on average.  Roads are exempt (r204c), which
        makes them worth far more than their length suggests.  Because the cost
        depends on the hex you leave, the graph is directed, so this is a
        Dijkstra run backwards from the target.

        The result is keyed on the party's speed (r204a: a mounted party moves
        two hexes a day), so buying a horse makes every cached route collapse to
        half its length.
        """
        speed = max(1, self.game.speed())
        key = (target, speed)
        cached = self._travel.get(key)
        if cached is not None:
            return cached
        g = self.game
        roads = g.road_sides
        dist = {target: 0.0}
        heap = [(0.0, target)]
        while heap:
            d, h = heapq.heappop(heap)
            if d > dist.get(h, 1e9) + 1e-9:
                continue
            for nb in g.model.neighbors(h).values():
                step = (1.0 if frozenset((nb, h)) in roads else
                        1.0 / (1.0 - _p_lost(g.model.travel_terrain(nb)))) / speed
                nd = d + step
                if nd < dist.get(nb, 1e9) - 1e-9:
                    dist[nb] = nd
                    heapq.heappush(heap, (nd, nb))
        self._travel[key] = dist
        return dist

    # ------------------------------------------------------------ macro plan
    # Economics measured over 150 campaigns (_refs/gold_days.py): a ruin day
    # nets ~ +5.5 gold, a temple day nets ~ -5.5 gold.

    def nearest(self, kind, start=None):
        """Closest hex of `kind` from `start` as ``(hex, expected days)``."""
        start = start or self.game.hex
        pool = [h for h, p in self.game.features['places'].items()
                if p['kind'] == kind]
        if not pool:
            return None, 999.0
        h = min(pool, key=lambda x: (self.travel_days(x).get(start, 999.0), x))
        return h, self.travel_days(h).get(start, 999.0)

    def camp_days(self):
        """Days of r212 camping left once the party walks to a temple."""
        _, days = self.nearest('temple')
        return max(0, int(TOTAL_DAYS - self.game.day - days))

    def camp_days_left(self):
        """Days of the game still available, counting today."""
        return max(1, TOTAL_DAYS - self.game.day + 1)

    def horse_days_saved(self, hex_=None):
        """Expected travel days a mount would save, measured from `hex_`.

        r210 puts a horse dealer in front of the party on a hire roll of 5 or
        10 - 7/36 of the time - and r204a doubles the daily move once every
        survivor is mounted.  The cost is the day spent rolling; the payoff is
        half of whatever walking is still left.  A mount only pays for itself
        while there is more than about five days of travel remaining.
        """
        g = self.game
        hex_ = hex_ or g.hex
        if g.speed() > 1:
            return 0.0
        unmounted = sum(1 for c in self.party() if c.mount == 'none')
        if unmounted > 3 or g.gold < 10 * unmounted:
            return 0.0
        plan = self.plan()
        if not plan:
            return 0.0
        remaining = (self.travel_days(plan[1]).get(hex_, 999.0) +
                     self.travel_days(plan[2]).get(plan[1], 999.0))
        odds = DEALER_ODDS + (1 / 36.0 if g.news_bonus.get(hex_) else 0.0)
        return odds * remaining / 2.0 - 1.0

    def wants_horse(self):
        """Is a hire roll in this hex worth it for the chance of a mount?"""
        return self.horse_days_saved() > 0.0

    def camp_plan(self):
        """The DP-optimal temple action: 'rest', 'news' or an offering amount.

        ``src/camp_dp.py`` solves the camp exactly: 2d6 + 1 (for a 10+ gold
        sacrifice) + permanent omen + one-day omen + High Priest influence,
        with r209 news as the only other gold sink.  Food and lodging are free
        for an unaccompanied Prince (r216/r217 only roll for follower
        desertion), so gold is the only constraint.
        """
        g = self.game
        return camp_action(self.camp_days_left(), g.gold, g.offering_bonus,
                          g.omen_bonus, g.influence_bonus, g.wit >= 5)

    def camp_win_chance(self):
        """P(win) from the current temple position."""
        g = self.game
        return camp_value(self.camp_days_left(), g.gold, g.offering_bonus,
                         g.omen_bonus, g.influence_bonus, g.wit >= 5)

    def ruins_cap(self):
        """How much gold is worth mining before committing to a temple.

        ``_refs/ruin_target.py`` solves the ruin phase as a stopping problem
        against the exact camp DP and the measured ruins lottery (97.3%
        nothing, 1.75% 60 gold, 0.97% 500 gold): with ``c`` camp days left the
        break-even pile is ``~2.8 * c + 20`` gold.  Banking more than that is
        mining days thrown away; banking less leaves the camp unable to buy the
        10-gold sacrifice on the day a modifier is in play.
        """
        return min(GOLD_CEILING, int(2.8 * self.camp_days() + 20))

    def ruin_budget(self):
        """Ruin-search days this campaign can still afford.

        ``_refs/campaign_dp.py`` maximises ``camp(camp_days, gold)` `` over the
        split of the non-travel days, and the optimum is consistently
        ``R* ~= RUIN_RATIO * (mining + camping days)``.  Reconstructing the
        original pool from the days already mined keeps the target stable as
        the campaign runs down, so a ruin that yields nothing is abandoned on
        schedule instead of eating the whole campaign.
        """
        g = self.game
        plan = self.plan()
        if not plan:
            return 0
        _, ruin, temple = plan
        if g.hex == ruin:
            pool = (TOTAL_DAYS - g.day) - self.travel_days(temple).get(ruin, 999.0)
        else:
            pool = plan[0]
        pool += self.ruin_days
        return max(0, int(RUIN_RATIO * pool) - self.ruin_days)

    def mining(self):
        """True while digging at the planned ruin beats camping at the temple.

        ``camp_dp.ruin_should_mine`` solves the ruin lottery as a stopping
        problem against the exact camp DP, so the gold threshold falls as the
        remaining travel eats into the camp days instead of being a flat cap.
        The same test is applied from any hex - once the ruin is no longer
        worth digging, the bot heads for the temple and never doubles back.
        """
        g = self.game
        plan = self.plan()
        if not plan:
            return False
        ruin, temple = plan[1], plan[2]
        td = self.travel_days(temple).get(ruin, 999.0)
        days_left = TOTAL_DAYS - g.day + 1
        if g.hex != ruin:
            days_left -= self.travel_days(ruin).get(g.hex, 999.0)
        return camp_dp.ruin_should_mine(int(days_left), g.gold, td)

    def plan(self):
        """The ruin/temple pair this campaign should run on.

        Returns ``(camp_days, ruin_hex, temple_hex)`` for the pair that leaves
        the most days at a temple, so the party never backtracks.  Distances
        are expected travel days, not hex counts: a longer road route can beat
        a shorter swamp route by several days.
        """
        g = self.game
        best = None
        for r, p in g.features['places'].items():
            if p['kind'] != 'ruins':
                continue
            t, td = self.nearest('temple', r)
            camp = (TOTAL_DAYS - g.day) - self.travel_days(r).get(g.hex, 999.0) - td
            if best is None or camp > best[0]:
                best = (camp, r, t)
        return best

    def camping(self):
        """True when the party is parked at a temple farming r212.

        Once the party has committed to a temple it stays there: every day
        spent walking back to a ruin is a day of offerings lost, and the camp
        DP (_refs/camp_policy.py) shows a 1-gold offering beats a day of
        ruin-searching as soon as the party is already on the temple.  The only
        exception is a broke party with the mining budget still open and enough
        days left to dig, walk back and still camp.
        """
        g = self.game
        if g.place_kind(g.hex) != 'temple' or g.staff or g.helm \
                or g.altar_blessed_day is not None:
            return False
        # A camp with less than the 10 gold the winning sacrifice needs is not a
        # camp at all: the party is better off back at the ruin.
        if g.gold >= GOLD_GOAL or not self.mining():
            return True
        plan = self.plan()
        if not plan:
            return True
        t = self.travel_days(plan[1]).get(g.hex, 999.0)
        return (TOTAL_DAYS - g.day) - 2 * t < MIN_CAMP_DAYS

    def farming_ruins(self):
        """True when the bot is digging in a ruin to make gold.

        r208 is the only repeatable, high-yield income in the game: a 4 on
        the search roll opens e136 (a 500-gold treasure room) and a 6 opens
        e139 (wealth 25-60).  The search is a daily action with no exhaustion
        clause, so a broke party should keep searching until the camp is
        funded - but only while there are still enough days left to camp.
        """
        g = self.game
        return (g.place_kind(g.hex) == 'ruins'
                and self.mining()
                and self.camp_days() >= MIN_CAMP_DAYS)

    def gold_hungry(self):
        """How badly the bot needs gold right now (r212 needs 10)."""
        return self.game.gold < GOLD_GOAL

    def modifiers(self):
        """Is any +1/+3 in play for the r212 offering roll?"""
        g = self.game
        return bool(g.offering_bonus or g.omen_bonus or g.influence_bonus)

    def goal_hex(self):
        """Where the bot wants to head.

        The Staff of Command (r212) is the only way to win, so the campaign
        is a two-phase plan:

          1. mine the ruin that sits closest to a temple until the camp is
             funded (``ruins_cap``), then
          2. walk to that temple and stay there, offering every day.

        Nothing else in the game produces gold fast enough to matter, so
        towns and castles are only waypoints on the way to the ruin.
        """
        g = self.game
        if g.staff:
            return min(g.model.grid, key=lambda h: int(h[2:]))
        if g.altar_blessed_day is not None:
            # The High Altar blessing (e044) wins by reaching any north-bank
            # hex within 30 days, so head for the nearest one.
            return min(g.model.grid,
                       key=lambda h: (int(h[2:]), h)
                       if h in g.NORTH_OF_TRAGOTH else (9999, h))
        if g.helm:
            # The Royal Helm (e194) wins by returning to Ogon or Weshor.
            return min(g.HELM_WIN_HEXES,
                       key=lambda h: (self.travel_days(h).get(g.hex, 999.0), h))
        if self.camping() or self.farming_ruins():
            return g.hex                      # hold position and work
        plan = self.plan()
        # Broke and parked at a temple: the only way to get gold is a ruin.
        if g.place_kind(g.hex) == 'temple' and plan:
            return plan[1]
        if plan and plan[0] >= MIN_CAMP_DAYS and self.mining():
            return plan[1]                    # still mining: go to the ruin
        temples = [h for h, p in g.features['places'].items()
                   if p['kind'] == 'temple']
        if not temples:
            return None
        return min(temples, key=lambda h: (self.travel_days(h).get(g.hex, 999.0), h))

    # ------------------------------------------------------------ decisions
    def choose(self, prompt, record=True):
        """Pick the best option of `prompt`.

        `record=False` leaves the bot's memory untouched, so the front-end can
        preview the bot's choice without burning a "tried" or "used" entry.
        """
        opts = prompt.get('options') or []
        if not opts:
            return 0
        title = prompt.get('title', '')
        low = title.lower()

        if prompt.get('kind') == 'combat':
            return self._combat(len(opts))
        if prompt.get('kind') == 'encounter' or 'try again' in low:
            return self._encounter(prompt, record)

        if title.startswith('Move'):
            return self._move(prompt, record)
        if 'action in hex' in low:
            return self._action(prompt, record)
        if 'meal' in low:
            return self._food(prompt)
        if 'lodging' in low:
            return self._lodging(prompt)
        if 'hiring' in low:
            return self._hire(prompt)
        if 'horse' in low:
            return self._horses(prompt)
        if 'porter' in low or 'guide' in low:
            return self._porter(prompt)
        if 'offering' in low:
            return self._offering(prompt)
        if 'high priest' in low:
            return self._priest(prompt)
        if 'escape' in low:
            return self._escape(prompt)
        return 0

    def suggest(self, prompt):
        """Same as choose(), but without updating the bot's memory."""
        return self.choose(prompt, record=False)


    # ---- combat (r220)
    def _combat(self, n):
        c = self.game.combat
        if c is None or n < 2:
            return 0
        mine, theirs = _power(c.party), _power(c.foes)
        prince = next((p for p in c.party if p.prince), None)
        if prince and prince.wounds >= prince.endurance - 1:
            return 1                                  # the Prince must survive
        ratio = mine / max(1, theirs)
        if c.round >= 8 and ratio < 1.5:
            return 1                                  # a grinding fight is lost
        return 0 if ratio >= 1.0 - self.p['fight'] * 0.05 else 1

    # ---- encounters (r207, r311-r340)
    def _encounter(self, prompt, record=True):
        ev = self.game.pending_event or {}
        headers = ev.get('headers') or []
        opts = prompt['options']
        n = len(opts)
        if n <= 1:
            return 0
        theirs = _power(parse_foes(prompt['text']))
        # r225: defeating the band pays out its wealth, so a fight is worth
        # more when the opposition is rich.  Read the numbers straight from
        # the text so the bot never disturbs the game's dice.
        loot = sum(int(m) for m in WEALTH_RE.findall(prompt['text']))
        mine = self.my_power()
        wit = self.game.wit
        scores = []
        for i in range(n):
            h = (headers[i] if i < len(headers) else opts[i]['label']).lower()
            if 'fight' in h or 'attack' in h or 'battle' in h:
                s = self.p['fight'] + 5 * (mine / max(1, theirs))
                if theirs > mine * 1.5:
                    s -= 6
                else:
                    s += min(8, loot // 10)         # r225 loot
            elif 'evade' in h or 'escape' in h or 'flee' in h:
                s = self.p['flee'] + (2 if theirs > mine else 0)
            elif 'talk' in h or 'negotiate' in h or 'parley' in h or 'reason' in h:
                s = self.p['talk'] + wit + (2 if theirs > mine else 0)
            elif 'bribe' in h or 'pay' in h:
                s = 1 + (4 if self.game.gold >= 30 else 0)
            elif 'hide' in h:
                s = 3
            elif 'hire' in h:
                m = PAY_RE.search(opts[i]['label'])
                pay = int(m.group(1)) if m else 0
                s = 8 if len(self.party()) < 6 and self.game.gold >= 20 + pay * 3 else -3
            elif 'refuse' in h or 'decline' in h:
                s = 1
            else:
                s = 1
            if any(k in h for k in ('steal', 'theft', 'rob ')):
                s -= 6
            if 'surrender' in h:
                s -= 4
            if (ev.get('code'), h) in self.tried:
                s -= 6                                # don't retry a failed approach
            scores.append(s)
        best = max(range(n), key=lambda i: scores[i])
        if record:
            self.tried.add((ev.get('code'),
                            (headers[best] if best < len(headers) else '').lower()))
        return best

    # ---- travel (r204)
    def _move(self, prompt, record=True):
        g = self.game
        opts = prompt['options']
        goal = self.goal_hex()
        # Expected days *to the goal*, so dgoal[hid] is "days still to go".
        dgoal = self.travel_days(goal) if goal else {}
        here = dgoal.get(g.hex, 0.0)
        back = self.path[-2] if len(self.path) >= 2 else None
        best, best_score = 0, None
        for i, o in enumerate(opts):
            label = o['label']
            if 'Stop travelling' in label:
                if g.moves_left <= 0:
                    s = 100                          # nothing left to move
                elif self.camping() or self.farming_ruins():
                    s = 12                           # stay and keep working
                else:
                    s = -10                          # travelling is the point
            else:
                m = HEX_RE.search(label)
                hid = m.group(1) if m else None
                s = 0
                road = '[road]' in label
                if road:
                    s += 8                           # roads: no "getting lost"
                if '[river]' in label:
                    s -= 3
                if hid:
                    s += TERRAIN_SCORE.get(g.model.travel_terrain(hid), 0)
                    kind = g.place_kind(hid)
                    s += PLACE_SCORE.get(kind, 0)
                    if hid not in g.visited:
                        s += 4                       # new ground = more events
                    if hid == back:
                        s -= 8                       # stop ping-ponging
                    if goal and hid in dgoal:
                        # r204/r205: the real cost of a step is its expected
                        # days, not one hex.  Total = this step + what is left
                        # from there, so minimise that sum.
                        step = (1.0 if road else 1.0 / (1.0 - _p_lost(
                            g.model.travel_terrain(g.hex)))) / max(1, g.speed())
                        s -= 14 * (step + dgoal[hid])
                        s += 14 * here               # constant, keeps scores sane
                    if kind in ('town', 'castle') and (hid, 'hire') not in self.done:
                        # r210: a mount halves the rest of the walk, so a town
                        # on the route is worth a stop if the dealer odds pay
                        # for the day (_refs/horse_value.py: +9% win rate).
                        saved = self.horse_days_saved(hid)
                        if saved > 0:
                            s += 14 * saved
                    s -= self.p['caution'] * TERRAIN_RISK.get(
                        g.model.travel_terrain(hid), 0)
            if best_score is None or s > best_score:
                best, best_score = i, s
        m = HEX_RE.search(opts[best]['label'])
        if m and record:
            self.path.append(m.group(1))
        return best

    # ---- daily action (r203)
    def _action(self, prompt, record=True):
        g = self.game
        party = self.party()
        wounds = sum(c.wounds for c in party)
        wounded = wounds > 0
        kind = g.place_kind(g.hex)
        goal = self.goal_hex()

        # Camped at a temple with nobody to heal: the camp DP is exact, so let
        # it pick the day's action instead of the heuristic scores below.
        if kind == 'temple' and not wounded and self.camping():
            plan = self.camp_plan()
            for i, o in enumerate(prompt['options']):
                label = o['label'].lower()
                if (isinstance(plan, int) and 'offering' in label) or \
                        (plan == 'news' and 'news' in label) or \
                        (plan == 'rest' and 'rest' in label):
                    act = next((a for a, key in ACTION_KEYS if key in label), None)
                    if act and record:
                        self.done.add((g.hex, act))
                        self.used[(g.hex, act)] = self.used.get((g.hex, act), 0) + 1
                    return i

        best, best_score = 0, None

        for i, o in enumerate(prompt['options']):
            label = o['label'].lower()
            act = next((a for a, key in ACTION_KEYS if key in label), None)
            if 'travel' in label:
                s = self.p['travel']               # travel drives the whole game
                if self.camping() or self.farming_ruins():
                    s -= 20                        # do not leave the gold mine
                elif goal and goal != g.hex:
                    s += 12                        # the goal is elsewhere
            elif 'rest' in label:
                # r222 heals one wound per day, so a hurt party is worth a
                # day of the campaign: wounds cut endurance and make every
                # future r220 fight more lethal.
                s = self.p['rest']
                if wounded and kind in ('town', 'castle', 'temple'):
                    s += 6 * wounds
            elif 'news' in label:
                # r209: 5 gold buys 2d6+1 (+1 more with wit >= 5).  A 3 pays
                # 50 gold, a 4 gives the permanent +1 on every future r212
                # offering, an 8 halves the wealth.  src/camp_dp.py solves the
                # camp exactly and shows the permanent +1 is worth far more
                # than a 1-gold offering once the pile is big - but only while
                # there are enough camp days left to cash it in.
                s = self.p['news']
                if kind == 'temple' and not g.offering_bonus:
                    s += 24 if self.camp_plan() == 'news' else -16
                elif not g.offering_bonus:
                    s -= 16
            elif 'hire' in label:
                s = self.p['hire'] if len(party) < self.p['max_party'] \
                    and g.gold >= 25 else 2
                saved = self.horse_days_saved()
                if saved > 0:
                    # Beat the travel option by the expected days the mount
                    # saves; the day spent rolling is already in `saved`.
                    s = max(s, self.p['travel'] + 12 + 14 * saved)
            elif 'audience' in label:
                s = self.p['audience']             # r211 - gold or trouble
            elif 'offering' in label:
                # r212 is the win condition.  With no modifiers 2d6 can never
                # reach 14, so an offering is really a lottery ticket for the
                # High Priest's +3 (roll 12/13) and for tomorrow's +1 (roll 7);
                # 1 gold buys that lottery far more often per gold than 10.
                # src/camp_dp.py decides the exact amount day by day.
                if g.gold < 1:
                    s = 1                          # broke: go and earn gold
                elif g.gold < 10:
                    s = 12                         # too poor to camp here
                else:
                    s = 26 + 4 * self.modifiers()
                    if kind == 'temple':
                        plan = self.camp_plan()
                        if isinstance(plan, int):
                            s = 30
                        elif plan == 'news':
                            s = 14
                        else:
                            s = 8
            elif 'ruins' in label:
                # r208 - the best repeatable gold source in the game.  A dice
                # 4 (3/36) opens e136 (500 gold), and the search can be repeated
                # every day.  The ruin phase is bounded by _refs/campaign_dp.py:
                # once the time budget is spent the days are worth more at the
                # temple, even if the gold target was never reached.
                s = self.p['ruins']
                if self.mining():
                    s += 22
                else:
                    s -= 18                        # budget spent: go offer it
            elif 'cache' in label:
                s = 14
            elif 'raft' in label:
                s = 5
            elif 'end the day' in label:
                s = -6
                if kind == 'temple' and self.camping() and self.camp_plan() == 'rest':
                    s = 28                         # DP says bank the gold today
            else:
                s = 0
            if goal and g.hex == goal and 'travel' not in label:
                s += 4
            if act == 'cache' and (g.hex, act) in self.done:
                s -= 12                              # one-off per hex
            if act not in ('offering', 'ruins', 'travel'):
                s -= 5 * self.used.get((g.hex, act), 0)   # diminishing returns

            if best_score is None or s > best_score:
                best, best_score = i, s
        chosen = prompt['options'][best]['label'].lower()
        act = next((a for a, key in ACTION_KEYS if key in chosen), None)
        if act and record:
            self.done.add((g.hex, act))
            self.used[(g.hex, act)] = self.used.get((g.hex, act), 0) + 1
            if act == 'ruins':
                self.ruin_days += 1
        return best

    # ---- food (r215, r216)
    def _food(self, prompt):
        g = self.game
        m = NEED_RE.search(prompt['title'])
        need = int(m.group(1)) if m else len(g.living())
        opts = prompt['options']
        for i, o in enumerate(opts):
            if 'eat from stores' in o['label'].lower():
                return i
        # r216 starvation only rolls for follower desertion and only bites
        # followers' skill.  A party of just the Prince therefore loses
        # nothing by going without, and the gold saved is worth roughly
        # doubling the number of offerings the camp can afford.
        if len(self.party()) <= 1:
            for i, o in enumerate(opts):
                if 'hungry' in o['label'].lower():
                    return i
            return 0
        for i, o in enumerate(opts):
            if 'buy meals' in o['label'].lower() and g.gold >= need + self.p['buffer'] // 2:
                return i
        for i, o in enumerate(opts):
            if 'hunting' in o['label'].lower():
                return i
        return 0

    # ---- lodging (r217)
    def _lodging(self, prompt):
        opts = prompt['options']
        if len(opts) < 2:
            return 0
        m = GOLD_RE.search(opts[0]['label'])
        cost = int(m.group(1)) if m else 0
        # r217 rough sleeping rolls for desertion; the Prince cannot desert
        # himself, so an unaccompanied Prince sleeps rough for free.
        if len(self.party()) <= 1:
            return 1
        return 0 if self.game.gold >= cost + self.p['buffer'] // 2 else 1

    # ---- hiring (r210, r331-r340)
    def _hire(self, prompt):
        opts = prompt['options']
        if len(opts) < 2:
            return 0
        label = opts[0]['label']
        m = PAY_RE.search(label)
        pay = int(m.group(1)) if m else 0
        c = COUNT_RE.search(label)
        n = int(c.group(1)) if c else 1
        party = len(self.game.living())
        if pay == 0:
            return 0 if party < 8 else 1
        if party < 4 and self.game.gold >= 25 + pay * n * 3:
            return 0
        return 1

    # ---- horse dealer (r210)
    def _horses(self, prompt):
        """Buy horses: r204a doubles the daily move once *every* survivor is
        mounted, and _refs/macro_dp5.py shows halving the travel legs is worth
        about seven percentage points of win rate - far more than the 7-10 gold
        a horse costs.  So the bot pays for a full mount as soon as it can.
        """
        opts = prompt['options']
        decline = next((i for i, o in enumerate(opts)
                        if 'decline' in o['label'].lower()), len(opts) - 1)
        party = self.game.living()
        unmounted = sum(1 for c in party if c.mount == 'none')
        if unmounted == 0:
            return decline
        best, best_value = None, 0.0
        for i, o in enumerate(opts):
            m = BUY_RE.search(o['label'])
            if not m:
                continue
            n = int(m.group(1))
            price = int(GOLD_RE.search(o['label']).group(1)) // n
            if self.game.gold < n * price + 5:
                continue
            # A complete mount is worth far more than a partial one.
            value = 100 if n >= unmounted else 20 * n
            if value > best_value:
                best, best_value = i, value
        return best if best is not None else decline

    # ---- porters & guides (r210)
    def _porter(self, prompt):
        opts = prompt['options']
        for i, o in enumerate(opts):
            if 'guide' in o['label'].lower() and self.game.gold >= 12:
                return i
        for i, o in enumerate(opts):
            if 'porter' in o['label'].lower() and self.game.gold >= 6:
                return i
        return next((i for i, o in enumerate(opts)
                     if 'decline' in o['label'].lower()), len(opts) - 1)

    # ---- offerings (r212): the road to the Staff of Command
    def _offering(self, prompt):
        """r212 - the offering roll is 2 dice + 1 for 10+ gold + the modifiers.

        14+ is needed for the Staff of Command.  The only modifiers are the
        +1 for a 10-gold sacrifice, the permanent +1 won by seeking news
        (r209 result 4) and the one-day +1 (r212 result 7) / +3 (r212 result
        12/13), so 10 + 1 + 3 = 14 is the cheapest winning combination and it
        always needs a 10-gold offering on the winning day.

        A 1-gold offering can never reach 14 by itself, but it is the cheapest
        way to *trigger* the modifiers: a 7 (6/36) buys tomorrow's +1 and a
        12/13 (3/36) buys tomorrow's +3.  ``src/camp_dp.py`` solves the camp
        exactly over (days left, gold, modifiers) and ``_refs/camp_policy_sim.py``
        confirms it on the engine: 1 gold farms the modifiers cheaply, 10 gold
        is only worth burning when the pile can sustain it for every remaining
        camp day or when a modifier is already in play.

        A lone Prince pays nothing for food or lodging (r216/r217 only roll
        for follower desertion), so the reserve is only the followers' upkeep.
        """
        opts = prompt['options']
        g = self.game
        gold = g.gold
        followers = max(0, len(self.party()) - 1)
        reserve = 3 * followers                 # food + lodging for tomorrow
        plan = self.camp_plan()
        target = plan if isinstance(plan, int) else GOLD_GOAL
        best, best_gap = None, None
        for i, o in enumerate(opts):
            m = re.search(r'Offer (\d+) gold', o['label'])
            if not m:
                continue
            amount = int(m.group(1))
            if amount > gold:
                continue
            if gold - amount < reserve:
                continue
            gap = abs(amount - target)
            if best_gap is None or gap < best_gap:
                best, best_gap = i, gap
        if best is not None:
            return best
        return next((i for i, o in enumerate(opts)
                     if 'withdraw' in o['label'].lower()), 0)

    def _priest(self, prompt):
        """r212 result 12/13: the High Priest's +3 influence beats any clue.

        The clues are flavour; the influence is the only way to reach 14+ on
        the very next offering, so the bot always takes it.
        """
        opts = prompt['options']
        for i, o in enumerate(opts):
            if 'influence' in o['label'].lower():
                return i
        return 0

    # ---- escape choices (r312, r313)
    def _escape(self, prompt):
        opts = prompt['options']
        fight = next((i for i, o in enumerate(opts)
                      if 'stand and fight' in o['label'].lower()), None)
        if fight is None:
            return 0
        if self.my_power() >= 2 * max(1, _power(parse_foes(prompt['text']))) \
                and self.strategy != 'cautious':
            return fight
        return 0


def run(game, strategy='balanced', max_steps=6000):
    """Play a whole campaign with the given personality. Returns steps taken."""
    bot = Bot(game, strategy)
    return game.run_until_idle(max_steps=max_steps, chooser=bot.choose)




