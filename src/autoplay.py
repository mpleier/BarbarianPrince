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
import re
from collections import deque

from engine import parse_foes

STRATEGIES = ('cautious', 'balanced', 'aggressive')

HEX_RE = re.compile(r'->\s*(\d{4})')
NEED_RE = re.compile(r'need\s+(\d+)')
GOLD_RE = re.compile(r'(\d+)\s*gold')
PAY_RE = re.compile(r'for\s+(\d+)\s*gold/day')
COUNT_RE = re.compile(r'Hire all (\d+)')
BUY_RE = re.compile(r'Buy (\d+) horse')

# Travel Table (r207) terrain -> how pleasant / safe the hex is.
TERRAIN_SCORE = {'Farmland': 3, 'Countryside': 3, 'Forest': 2, 'Hills': 2,
                 'Mountains': -4, 'Swamp': -4, 'Desert': -6}
PLACE_SCORE = {'town': 4, 'castle': 4, 'temple': 6, 'ruins': 2,
               'camp': 1, 'pass': 1, 'marsh': -2}
TERRAIN_RISK = {'Mountains': 4, 'Desert': 5, 'Swamp': 3, 'Forest': 2,
                'Wasteland': 2, 'Farmland': 0, 'Countryside': 0, 'River': 1}

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
        self._dist = {}

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

    def camping(self):
        """True when the bot has parked itself at a temple to farm r212."""
        g = self.game
        return (g.place_kind(g.hex) == 'temple'
                and (g.gold >= 10 or g.offering_bonus))

    def goal_hex(self):
        """Where the bot wants to head.

        The Staff of Command (r212) is the only way to win: at a temple the
        offering roll is 2 dice + 1 (for 10+ gold) + 1 (favourable omens from
        the previous day), and 14+ is required.  Since 12+1+1 = 14, the bot
        must reach a temple with at least 10 gold and keep trying there.
        """
        g = self.game
        if g.staff:
            return min(g.model.grid, key=lambda h: int(h[2:]))
        if self.camping():
            return g.hex                      # hold position and keep offering
        d = self.distances(g.hex)
        places = g.features['places']
        pool = [h for h, p in places.items() if p['kind'] == 'temple']
        if not pool:
            pool = [h for h, p in places.items()
                    if p['kind'] in ('town', 'castle')]
        if not pool:
            return None
        return min(pool, key=lambda h: (d.get(h, 999), h))

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
        mine = self.my_power()
        wit = self.game.wit
        scores = []
        for i in range(n):
            h = (headers[i] if i < len(headers) else opts[i]['label']).lower()
            if 'fight' in h or 'attack' in h or 'battle' in h:
                s = self.p['fight'] + 5 * (mine / max(1, theirs))
                if theirs > mine * 1.5:
                    s -= 6
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
        # BFS *from the goal*, so dist[hid] is "hexes still to go" from hid.
        dgoal = self.distances(goal) if goal else {}
        here = dgoal.get(g.hex, 0)
        back = self.path[-2] if len(self.path) >= 2 else None
        best, best_score = 0, None
        for i, o in enumerate(opts):
            label = o['label']
            if 'Stop travelling' in label:
                if g.moves_left <= 0:
                    s = 100                          # nothing left to move
                elif self.camping():
                    s = 12                           # stay and keep offering
                else:
                    s = -10                          # travelling is the point
            else:
                m = HEX_RE.search(label)
                hid = m.group(1) if m else None
                s = 0
                if '[road]' in label:
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
                        s += 12 * (here - dgoal[hid])  # progress towards goal
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
        wounded = any(c.wounds > 0 for c in party)
        kind = g.place_kind(g.hex)
        goal = self.goal_hex()
        best, best_score = 0, None
        for i, o in enumerate(prompt['options']):
            label = o['label'].lower()
            act = next((a for a, key in ACTION_KEYS if key in label), None)
            if 'travel' in label:
                s = self.p['travel']               # travel drives the whole game
                if self.camping():
                    s -= 20                        # do not leave the temple
            elif 'rest' in label:
                s = 13 if wounded and kind in ('town', 'castle', 'temple') else 3
            elif 'news' in label:
                s = self.p['news'] if g.gold >= 5 or g.wit >= 5 else 4
            elif 'hire' in label:
                s = self.p['hire'] if len(party) < self.p['max_party'] \
                    and g.gold >= 25 else 2
            elif 'audience' in label:
                s = self.p['audience']             # r211 - gold or trouble
            elif 'offering' in label:
                # r212 is the win condition: 14+ needs 10+ gold and an omen.
                if g.gold >= 10:
                    s = 30 if g.offering_bonus else 26
                else:
                    s = 4                          # go and earn gold first
            elif 'ruins' in label:
                s = self.p['ruins']                # r214 - loot, but r215 hurts
            elif 'cache' in label:
                s = 14
            elif 'raft' in label:
                s = 5
            elif 'end the day' in label:
                s = -6
            else:
                s = 0
            if goal and g.hex == goal and 'travel' not in label:
                s += 4
            if act in ('ruins', 'cache') and (g.hex, act) in self.done:
                s -= 12                              # one-off per hex
            if act != 'offering':
                s -= 5 * self.used.get((g.hex, act), 0)   # diminishing returns

            if best_score is None or s > best_score:
                best, best_score = i, s
        chosen = prompt['options'][best]['label'].lower()
        act = next((a for a, key in ACTION_KEYS if key in chosen), None)
        if act and record:
            self.done.add((g.hex, act))
            self.used[(g.hex, act)] = self.used.get((g.hex, act), 0) + 1
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
        opts = prompt['options']
        decline = next((i for i, o in enumerate(opts)
                        if 'decline' in o['label'].lower()), len(opts) - 1)
        unmounted = sum(1 for c in self.game.living() if c.mount == 'none')
        if unmounted == 0:
            return decline
        best = None
        for i, o in enumerate(opts):
            m = BUY_RE.search(o['label'])
            if not m:
                continue
            n = int(m.group(1))
            price = int(GOLD_RE.search(o['label']).group(1)) // n
            if n <= unmounted and self.game.gold >= n * price + 20:
                best = i
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
        """r212 - the offering roll is 2 dice + 1 for 10+ gold + the omen bonus.

        14+ is needed for the Staff of Command and 12+1+1 = 14, so 10 gold is
        exactly the right amount: it is the minimum that buys the +1, it also
        lifts the lowest possible roll to 3 (a roll of 2 closes the temple and
        arrests the party), and anything above 10 is simply wasted.
        """
        opts = prompt['options']
        gold = self.game.gold
        reserve = 2 * max(1, len(self.party()))   # food & lodging for tomorrow
        best, best_gap = None, None
        for i, o in enumerate(opts):
            m = re.search(r'Offer (\d+) gold', o['label'])
            if not m:
                continue
            amount = int(m.group(1))
            if amount > gold:
                continue
            if amount < 10 and gold - amount < reserve:
                continue
            gap = abs(amount - 10)
            if best_gap is None or gap < best_gap:
                best, best_gap = i, gap
        if best is not None:
            return best
        return next((i for i, o in enumerate(opts)
                     if 'withdraw' in o['label'].lower()), 0)

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




