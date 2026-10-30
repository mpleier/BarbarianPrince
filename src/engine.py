"""Rules-accurate Barbarian Prince game engine (r201-r228 core loop).

The engine is UI-agnostic: it maintains a queue of *prompts* that any interface
(tkinter GUI, CLI, tests) can render and answer.

Prompt kinds
  'encounter'  an event with a talk / evade / fight option matrix
  'combat'     a round-by-round battle (r220)
  'choice'     a plain decision
  'info'       text the player must acknowledge
"""
import json
import os
import random
import re

from game_model import GameModel

from resource import DATA  # bundled data/, frozen or from source

GAME_DAYS = 70
TARGET_GOLD = 500

# r220c Combat Results Table
COMBAT_TABLE = {-1: 1, 3: 1, 5: 1, 8: 1, 11: 1,
                10: 2, 12: 2, 13: 2, 17: 2,
                14: 3, 16: 5, 18: 5, 19: 5, 20: 6}

# r330 Battle Reference
BATTLE_REFERENCE = {2: 'r310', 3: 'r309', 4: 'r308', 5: 'r307', 6: 'r306',
                    7: 'r305', 8: 'r304', 9: 'r303', 10: 'r302', 11: 'r301',
                    12: 'r300'}

# r341 Conversation
CONVERSATION = {2: 'r310', 3: 'r308', 4: 'r305', 5: 'r331', 6: 'r332', 7: 'r333',
                8: 'r338', 9: 'r335', 10: 'r336', 11: 'r340', 12: 'r334'}

# r342 General Inquiry
INQUIRY = {2: 'r309', 3: 'r330', 4: 'r340', 5: 'r306', 6: 'r325', 7: 'r341',
           8: 'r333', 9: 'r339', 10: 'r337', 11: 'r338', 12: 'r336'}

REF_RE = re.compile(r'\b([re]\d{3})\b')
GOLD_TEXT_RE = re.compile(r'(?:gain|find|worth|receive)\s+(\d+)\s+gold', re.I)
DIE_TABLE_RE = re.compile(r'roll one die|one die rolled|die roll for', re.I)
STAT_RE = re.compile(r'combat skill (\d+)(?:,\s*(?:and\s*)?endurance (\d+))?'
                     r'(?:,\s*wealth (\d+))?')
DIRECTIONS = ['N', 'NE', 'SE', 'S', 'SW', 'NW']
HUNT_TERRAIN = ('Farmland', 'Countryside', 'Forest', 'Hills')
POPULATED = ('town', 'castle', 'temple')
# r208 ruins search and r213 rafting tables are keyed by the dice total.
with open(os.path.join(DATA, 'tables.json'), encoding='utf-8') as _f:
    _TABLES = json.load(_f)

RUINS = {int(k): v for k, v in _TABLES['ruins_search'].items()}
RAFTING = {int(k): v for k, v in _TABLES['raft_travel_events'].items()}

# r213: a raft covers three river hexsides a day downriver, two upriver.
RAFT_SPEED = 3
RAFT_UPSTREAM = 2

# An option cell ends with a booklet reference.  The OCR occasionally renders
# 'r309' as 'i309', so that variant is accepted and normalised later.
OPTION_REF_RE = re.compile(r'^[rcei]\d{3}$')
OPTION_VERBS = {
    'pass', 'converse', 'conversation', 'inquiry', 'looter', 'looters',
    'hireling', 'hirelings', 'plead', 'bribe', 'escape', 'escapee', 'hide',
    'attack', 'attacked', 'surprise', 'surprised', 'battle', 'ally',
    'arrest', 'arrested', 'audience', 'roll', 'surrender', 'rob', 'steal',
    'negotiate', 'parley', 'reason', 'refuse', 'decline', 'flee', 'fight',
    'ignore', 'pursue', 'pursued', 'ambush', 'capture', 'demand', 'offer',
}


def normalise_ref(ref):
    """Repair the booklet's misprinted references (i309 -> r309)."""
    if ref and ref[0] == 'i':
        return 'r' + ref[1:]
    return ref





def threshold(spec):
    """'10+' -> 10, 'never' -> None, '-' -> None."""
    if not spec:
        return None
    m = re.search(r'\d+', spec)
    return int(m.group(0)) if m else None


def _split_cells(tokens, n_headers):
    """Split one matrix row into its header-aligned cells.

    Each cell is a label followed by a reference.  When a row carries fewer
    references than headers (e002 roll 7, e130 roll 4) the booklet has left a
    cell without a reference, so a bare option verb starts a new cell.

    The OCR sometimes glues a label to its reference ('hider318' in e050), so a
    token ending in a reference is split in two first.
    """
    expanded = []
    for tok in tokens:
        m = re.match(r'^([A-Za-z][A-Za-z-]*)([rceiRCei]\d{3})$', tok)
        if m:
            expanded.extend([m.group(1), m.group(2)])
        else:
            expanded.append(tok)
    tokens = expanded

    split_on_verb = sum(1 for t in tokens if OPTION_REF_RE.match(t)) < n_headers
    cells = []
    label = []
    for tok in tokens:
        if OPTION_REF_RE.match(tok):
            lab = ' '.join(label).strip('*').strip()
            cells.append((lab or 'option', normalise_ref(tok)))
            label = []
            continue
        if split_on_verb and label and tok.strip('*').lower() in OPTION_VERBS:
            lab = ' '.join(label).strip('*').strip()
            if lab:
                cells.append((lab, None))
            label = [tok]
            continue
        label.append(tok)
    if label:
        lab = ' '.join(label).strip('*').strip()
        if lab:
            cells.append((lab, None))
    return cells


def _pad_cells(cells, n, foot_col):
    """A row with fewer cells than headers: the missing ones do nothing.

    A single cell in a footnote row belongs to the footnoted column (e002
    roll 7 'escape mtd' is an *evade* option, not a talk option).  Extra
    cells are the footnote text bleeding into the row.
    """
    if len(cells) > n:
        return cells[:n]
    if len(cells) == 1 and foot_col is not None and 0 <= foot_col < n:
        return ([('nothing happens', None)] * foot_col
                + cells
                + [('nothing happens', None)] * (n - foot_col - 1))
    return cells + [('nothing happens', None)] * (n - len(cells))


def parse_options(text):
    """Extract the 'die roll / talk / evade / fight' option matrix of an event.

    The booklet writes the matrix as a header row ('die roll talk *evade fight')
    followed by one row per die roll, each row holding one label + reference per
    header.  A '*' is only a footnote marker, so it must not be treated as the
    end of the matrix - doing so silently dropped the evade/fight columns and
    left the player (or the bot) with a single 'talk' option.  A bare '*' or a
    'Note:' line *does* end the matrix: it is the footnote, not a row.

    Some events (e050) put rules prose between the lead-in and the matrix, and
    that prose mentions 'the die roll' itself, so every candidate header row is
    tried and the one whose headers actually look like option verbs wins.
    """
    best = _best_option_candidate(text)
    return best[:3] if best else None


def _best_option_candidate(text):
    """(headers, rows, note, start) of the best matrix, or None.

    ``start`` is the offset of the 'die roll' header inside ``text``, which is
    what ``split_event`` needs to cut the prose away from the table.

    Most entries introduce the matrix with "the options are" or "select your
    option", but some (e006 "select one of the three options below", e071
    "You have three options:") do not, so the lead-in is optional.  A candidate
    must then look like a table: at most six columns, at least one option verb
    among the headers, and two or more rows.
    """
    m = re.search(r'(options are|select your option)', text, re.I)
    start_from = m.end() if m else 0
    best = None
    best_score = None
    for header in re.finditer(r'\bdie\s+roll\b', text[start_from:], re.I):
        start = start_from + header.start()
        parsed = _option_matrix(text, start_from + header.end())
        if not parsed:
            continue
        headers, rows, note = parsed
        if len(headers) < 2 or len(rows) < 2 or len(headers) > 6:
            continue
        verbs = sum(1 for h in headers
                    if h.lower().strip('*-.,') in OPTION_VERBS)
        if verbs < 1:
            continue
        # Prefer the candidate whose headers are *mostly* option verbs: a run of
        # prose can contain several verbs by accident but is mostly filler.
        score = (2 * verbs - len(headers), len(rows))
        if best_score is None or score > best_score:
            best, best_score = (headers, rows, note, start), score
    return best


def split_event(text):
    """(prose, options) - an event text with its option matrix pulled out.

    The booklet prints the matrix inside the entry, so the raw text reads
    "... die roll Negotiate * evade fight 1 surprised r308 ..." when shown in a
    reference window.  ``options`` is ``{'headers', 'rows', 'note'}`` or None.
    """
    best = _best_option_candidate(text)
    if not best:
        return text.strip(), None
    headers, rows, note, start = best
    prose = text[:start].rstrip()
    return prose, {'headers': headers, 'rows': rows, 'note': note}


def _option_matrix(text, start):
    """Parse the matrix whose header row ends at ``start``."""
    tokens = text[start:].split()
    i = 0
    headers = []
    foot_col = None
    while i < len(tokens) and not tokens[i].isdigit():
        raw = tokens[i]
        head = raw.strip('*').strip()
        i += 1
        if not head:
            continue
        if '*' in raw:
            foot_col = len(headers)
        headers.append(head)
    if not headers:
        return None

    rows = []
    while i < len(tokens) and tokens[i].isdigit() and int(tokens[i]) <= 12:
        roll = int(tokens[i])
        i += 1
        span = i
        while span < len(tokens):
            tok = tokens[span]
            if tok.lower().startswith('note:'):
                break
            if tok.isdigit() and int(tok) <= 12:
                break
            # A footnote marker ends the row, but only once the row has already
            # produced a cell: in e130 roll 4 the row *opens* with '**audience'.
            if tok == '*' or (tok.startswith('**')
                              and any(OPTION_REF_RE.match(t) for t in tokens[i:span])):
                break
            span += 1
        cells = _split_cells(tokens[i:span], len(headers))
        if not cells:
            break
        rows.append((roll, _pad_cells(cells, len(headers), foot_col)))
        i = span
    note = ' '.join(tokens[i:]).strip()
    return headers, rows, note



def die_entries(text):
    """Return the '1-x; 2-y; ...' entries of a 'roll one die' table, if any.

    Entries may list several rolls for one outcome ('5,6-Town Mayor'), so each
    entry is returned as (list_of_rolls, outcome_text).
    """
    m = DIE_TABLE_RE.search(text)
    if not m:
        return None
    entries = []
    for chunk in text[m.end():].split(';'):
        d = re.search(r'(\d+(?:,\s*\d+)*)\s*-\s*(.+)', chunk)
        if d:
            entries.append(([int(x) for x in d.group(1).split(',')],
                            d.group(2).strip()))
    return entries if len(entries) >= 3 else None


def parse_foes(text, rng=None):
    """Parse the stat block(s) of the characters an event describes.

    `rng` is the game's own generator; passing it keeps a seeded campaign
    reproducible instead of borrowing the global `random` state.
    """
    rng = rng or random
    stats = [(int(s), int(e) if e else 5, int(w) if w else 0)
             for s, e, w in STAT_RE.findall(text)]
    if not stats:
        return []
    count = 1
    low = text.lower()
    if 'roll one die for the number of' in low:
        count = rng.randint(1, 6)
    elif 'roll two dice for the number of' in low:
        count = rng.randint(1, 6) + rng.randint(1, 6)
    elif 'number in the group is one die roll plus one' in low:
        count = rng.randint(1, 6) + 1
    else:
        m = re.search(r'(\d+)\s+(?:men|warriors|guards|tribesmen|bandits|horsemen|'
                      r'assassins|constables|priests|monks|witches|magicians|wizards|'
                      r'dwarves|elves|orcs|giants|trolls|centaurs|amazons|mercenaries|'
                      r'henchmen|retainers|riders|thugs|soldiers|pirates|nomads|'
                      r'bodyguards|guardsmen|peasants|villagers|outlaws|robbers)\b', low)
        if m:
            count = int(m.group(1))
    return [Character(f'Foe {i + 1}', *(stats[i % len(stats)])) for i in range(count)]



class Character:
    """Any character: the Prince, followers, or encountered foes."""

    def __init__(self, name, skill, endurance, wealth=0, mount='none',
                 guide=False, pay=0, prince=False, kind=''):
        self.name = name
        self.skill = skill
        self.endurance = endurance
        self.wounds = 0
        self.wealth = wealth
        self.mount = mount          # 'none' | 'horse' | 'winged'
        self.guide = guide
        self.pay = pay
        self.prince = prince
        # r211: 'priest' or 'magician' - the calling decides how temples and
        # the Baron of Huldra treat the party.  Names alone are unreliable once
        # a character joins as "Hired 1", so the event that recruits them
        # records the calling here.
        self.kind = kind
        self.alive = True
        self.starved = 0
        self.poisoned = 0
        self.unreliable = False
        self.town_leaver = False

    def feed(self, portions=1):
        """r216b: a normal meal undoes one day of starvation (two undo two).

        Triple or larger meals have no extra effect, so ``portions`` is capped
        at two.
        """
        self.starved = max(0, self.starved - max(0, min(2, portions)))

    @property
    def effective_skill(self):
        # r221b: an unconscious character is helpless - combat skill zero.
        if self.unconscious:
            return 0
        return max(0, self.skill - self.starved)

    @property
    def remaining(self):
        return self.endurance - self.wounds

    @property
    def serious(self):
        return self.wounds * 2 >= self.endurance

    @property
    def unconscious(self):
        return self.wounds == self.endurance - 1

    @property
    def dead(self):
        return self.wounds >= self.endurance

    def load_capacity(self):
        cap = 10
        for _ in range(self.starved):
            cap //= 2
        return cap

    def __repr__(self):
        return (f'{self.name} (skill {self.skill}, endurance {self.endurance}, '
                f'wounds {self.wounds}, mount {self.mount})')



class Combat:
    """r220 - round-by-round combat."""

    def __init__(self, party, foes, rng, party_first=True, name='Battle',
                 surprise=None, note=None):
        self.party = [c for c in party if not c.dead]
        self.foes = [c for c in foes if not c.dead]
        self.original_foes = list(self.foes)   # r225: loot is taken from the
        self.rng = rng                         # whole encountered band
        self.party_first = party_first
        self.surprise = surprise            # 'party' | 'foes' | None
        self.name = name
        self.round = 0
        self.over = False
        self.result = None
        self.log = []
        self.note = note or (lambda t: None)

    def modifiers(self, striker, target):
        total = 0
        if target.wounds * 2 >= target.endurance:
            total += 2
        if striker.wounds >= 1:
            total -= 1
        if striker.wounds * 2 >= striker.endurance:
            total -= 1
        return total

    def strike(self, striker, target):
        base = striker.effective_skill - target.effective_skill
        dice = self.rng.randint(1, 6) + self.rng.randint(1, 6)
        total = base + dice + self.modifiers(striker, target)
        wounds = COMBAT_TABLE.get(total, 0)
        if wounds:
            target.wounds += wounds
            self.log.append(f'{striker.name} ({total}) strikes {target.name}: '
                            f'{wounds} wound(s) [{target.wounds}/{target.endurance}]'
                            + (' -> dead' if target.dead else ''))
        else:
            self.log.append(f'{striker.name} ({total}) strikes {target.name}: missed')
        return wounds

    def pairing_of(self, attackers, defenders):
        """r220b - strongest vs strongest; extras pile onto one opponent."""
        attackers = sorted([c for c in attackers if not c.dead],
                           key=lambda c: -c.effective_skill)
        defenders = sorted([c for c in defenders if not c.dead],
                           key=lambda c: -c.effective_skill)
        if not attackers or not defenders:
            # one side was already wiped out this round: nobody to strike
            return []
        return [(a, defenders[i % len(defenders)])
                for i, a in enumerate(attackers)]

    def round_side(self, attackers, defenders):
        for striker, target in self.pairing_of(attackers, defenders):
            if not target.dead and not striker.dead:
                self.strike(striker, target)
        for c in attackers + defenders:
            if c.dead:
                c.alive = False

    def rout_possible(self):
        return any(f.skill < 9 and f.endurance < 9 for f in self.foes)

    def step(self):
        """Resolve one combat round (r220a)."""
        if self.over:
            return self.result
        self.round += 1
        self.log.append(f'--- round {self.round} ---')
        if self.surprise and self.round == 1:
            strikers = self.party if self.surprise == 'party' else self.foes
            targets = self.foes if self.surprise == 'party' else self.party
            for s in list(strikers):
                if not s.dead and targets:
                    self.strike(s, targets[0])
            self.surprise = None
            for c in self.party + self.foes:
                if c.dead:
                    c.alive = False
        first, second = ((self.party, self.foes) if self.party_first
                         else (self.foes, self.party))
        self.round_side(first, second)
        if self.party and self.foes:
            self.round_side(second, first)
        survivors = [c for c in self.party if c.alive and not c.dead]
        foes_left = [c for c in self.foes if c.alive and not c.dead]
        killed = len(self.foes) - len(foes_left)
        self.party, self.foes = survivors, foes_left
        if killed and self.foes and self.rout_possible():
            die = self.rng.randint(1, 6)
            if die == 6:
                self.note('The enemy routs and flees!')
                self.foes = []
                self.over, self.result = True, 'foes routed'
            else:
                self.log.append(f'Rout check: die {die} - they stand their ground.')
        if not self.foes:
            self.over, self.result = True, 'party wins'
        elif not self.party:
            self.over, self.result = True, 'party wiped out'
        return self.result

    def attempt_escape(self):
        """r220e - all or none escape; no strikes that round."""
        self.round += 1
        die = self.rng.randint(1, 6)
        if die >= 4:
            self.over = True
            self.result = 'party escaped'
            return True, die
        self.log.append(f'Escape attempt fails (die {die}).')
        return False, die



class Game:
    """The Barbarian Prince rules engine."""

    ACTIONS = [
        ('Travel to a new hex (r204)', 'travel'),
        ('Rest and heal wounds (r222)', 'rest'),
        ('Seek news & information (r209)', 'news'),
        ('Seek to hire followers (r210)', 'hire'),
        ('Seek an audience (r211)', 'audience'),
        ('Submit an offering (r212)', 'offerings'),
        ('Search the ruins (r208)', 'ruins'),
        ('Recover a hidden cache (r214)', 'cache'),
        ('Raft down the river (r213)', 'raft'),
    ('Buy food stores (r215e)', 'buyfood'),
        ('Follow encountered characters (r219)', 'follow'),
    ]

    # The 20 hexes on the north bank of the Tragoth River.  Winning requires
    # carrying the Staff of Command into one of these (r212 result 14+), or
    # reaching any of them within 30 days of the High Altar blessing (e044).
    NORTH_OF_TRAGOTH = frozenset({
        '0101', '0201', '0301', '0302', '0501', '0502', '0601', '0701',
        '0801', '0901', '1001', '1101', '1201', '1301', '1501', '1601',
        '1701', '1801', '1901', '2001',
    })

    # The Royal Helm of the Northlands (e194) wins the game when the Prince
    # returns to either of these towns with it.
    HELM_WIN_HEXES = frozenset({'0101', '1501'})

    # Days the High Altar blessing (e044 roll 6) lasts before it fades.
    ALTAR_BLESSING_DAYS = 30

    def __init__(self, model=None, features=None, seed=None, start_hex='0101'):
        self.model = model or GameModel.load()
        if features is None:
            with open(os.path.join(DATA, 'features.json'), encoding='utf-8') as f:
                features = json.load(f)
        self.features = features
        # JSON stores hexside pairs as lists; keep frozenset copies for O(1) tests.
        self.road_sides = {frozenset(p) for p in features.get('road_sides', ())}
        self.river_sides = {frozenset(p) for p in features.get('river_sides', ())}
        # r213: "a|b" -> the hex the water flows to (top to bottom on the map)
        self.river_flow = dict(features.get('river_flow', {}))
        # r213: "a|b" -> the river's name, used for the r205d crossing state
        self.river_names = dict(features.get('river_names', {}))
        self.rng = random.Random(seed)
        self.log = []
        self.prompts = []
        self.day = 1
        self.hex = start_hex
        self.gold = 0
        self.food = 0
        self.caches = {}
        self.visited = {start_hex}
        # r218/e050: a town the party escaped from is a place it is "wanted",
        # so it no longer counts as a friendly visit.
        self.escaped_from = set()
        self.items = []
        self.raft = False
        self.raft_days = 0
        self.raft_dir = None        # r213: 'down' or 'up' for the current day
        self.news_bonus = {}
        self.offering_bonus = 0     # r209 result 4: permanent +1 at the temple
        self.omen_bonus = 0         # r212 result 7: +1 on the next offering
        self.influence_bonus = 0    # r212 result 12/13: +3 on the next offering
        self.peak_gold = 0          # highest gold ever held, for the win report
        self._ruins_retry = 0       # r208/e132 organised-search re-rolls
        self.free_lodging = False
        self.staff = False
        self.helm = False
        self.altar_blessed_day = None    # day the e044 roll-6 blessing was won
        self.imprisoned = None      # None | 'e061' | 'e062' | 'e063'
        self.prison_days = 0
        self.party = []
        self.combat = None
        self.pending_event = None
        self.event_kind = None      # r204f: 'talk' / 'combat' allow travelling on
        # r205d: (hex, river) pairs the party has already crossed - from those
        # hexes the far bank can be entered without another crossing check
        self.crossed = set()
        self.action = None
        self.phase = 'action'
        self.moves_left = 0
        self.flying = False
        self.game_over = False
        self.won = False
        self.reason = ''
        self.wit = self.d1()
        if self.wit == 1:
            self.wit = 2
        self.start()

    # ------------------------------------------------------------ dice & logging
    def d1(self):
        return self.rng.randint(1, 6)

    def d2(self):
        return self.rng.randint(1, 6) + self.rng.randint(1, 6)

    def note(self, text):
        self.log.append(text)

    def treasure_roll(self, code):
        """r226 Treasure Table: wealth code + one die -> gold (and maybe an item)."""
        table = {int(r['code']): r['results'] for r in self.model.tables['treasure_table']}
        code = int(code)
        if code not in table:
            code = max(0, min(110, code))
            if code not in table:
                return 0, None
        raw = table[code][(self.d1() - 1) % len(table[code])]
        raw = str(raw)
        item = None
        event = None
        if '+' in raw:
            # A letter code: a special possession was found.  Roll again on the
            # Treasure Table and read the matching letter line for the specific
            # event that describes the new possession (r226).
            gold, letter = raw.split('+')
            lines = self.model.tables.get('special_possession_lines', {})
            options = lines.get(letter, [])
            if options:
                event = options[(self.d1() - 1) % len(options)]
            item = f'Special possession {letter}'
        else:
            gold = raw
        return int(gold), item, event

    def gain_treasure(self, gold, item, event):
        """Apply loot from a Treasure Table result (r226) and resolve any
        special possession.

        The Royal Helm of the Northlands (e194) is the only possession with a
        standing effect: it raises the Prince's wit & wiles by one (+1) and
        lets him win by returning to Ogon or Weshor (checked in ``finish_day``).

        After gaining treasure, checks whether the party exceeds load capacity
        (r206). If so, automatically caches excess gold to bring loads within
        the party's carrying capacity.
        """
        self.gold += gold
        if item:
            self.items.append(item)
        if event == 'e194' and not self.helm:
            self.helm = True
            self.wit += 1
            self.note('You found the Royal Helm of the Northlands (e194).')
            self.note('Its possession raises your wit & wiles by one (+1), and '
                      'it wins the game if you return to Ogon (0101) or Weshor '
                      '(1501) with it.')
        # r206 - post-treasure load check: auto-cache if over capacity
        used = self.current_loads()
        cap = self.max_capacity()
        if used > cap:
            self.note(f'Treasure pushes the party over capacity '
                      f'({used}/{cap} loads). Auto-caching excess gold.')
            self._auto_cache_loads(used - cap)

    # ------------------------------------------------------------ party helpers
    def living(self):
        return [c for c in self.party if c.alive and not c.dead]

    def prince(self):
        for c in self.party:
            if c.prince:
                return c
        return None

    def has_guide(self):
        return any(c.guide for c in self.living())

    def speed(self):
        """r204a - 3 hexes if the whole party has winged mounts,
        2 if everyone is mounted, otherwise 1 (on foot)."""
        party = self.living()
        if not party:
            return 1
        if all(c.mount == 'winged' for c in party):
            return 3
        if all(c.mount != 'none' for c in party):
            return 2
        return 1


    def start(self):
        # __init__ already starts the game; calling start() again (as tests and
        # the CLI do) must not add a second Prince.
        if any(c.prince for c in self.party):
            return
        self.party.append(Character('Cal Arath (the Prince)', 8, 9, 2,
                                    prince=True))
        # r202: the Prince's wealth code is 2 - roll the Treasure Table (r226)
        # for the coins he grabbed on the way out (0-4 gold).
        gold, item, _event = self.treasure_roll(2)
        self.gold = gold
        self.note(f'The Barbarian Prince begins his quest in hex {self.hex}. '
                  f'Wit & wiles = {self.wit}; starting purse {gold} gold (r202).')
        if item:
            self.items.append(item)

    def place(self, hid):
        return self.features['places'].get(hid)

    def place_name(self, hid):
        p = self.place(hid)
        return p['name'] if p else None

    def north_of_tragoth(self, hid=None):
        """True if ``hid`` (default: the Prince's current hex) is on the north
        bank of the Tragoth River - the region the Staff of Command must be
        carried into to win (r212 result 14+)."""
        return (hid if hid is not None else self.hex) in self.NORTH_OF_TRAGOTH

    def place_kind(self, hid):
        p = self.place(hid)
        return p['kind'] if p else None

    def cache(self, amount):
        """r214 - bury gold in the current hex as a hidden cache."""
        if amount <= 0 or amount > self.gold:
            return False
        self.gold -= amount
        code = min(110, max(1, (amount + 99) // 100))
        self.caches[self.hex] = (code, amount)
        self.note(f'Cached {amount} gold in hex {self.hex}.')
        return True

    # ------------------------------------------------------------ transport (r206)
    # r206a load weights:
    #   food  = 1 load per unit
    #   gold  = 1 load per 100 gp (or fraction thereof)
    #   person carried = 20 loads
    #   weapons do not count
    # r206b transport capacities:
    #   man on foot  = 10 loads
    #   mount        = 30 loads (or a rider (20 loads) + 10 loads of cargo)
    def current_loads(self):
        """r206a - calculate the total loads currently carried by the party."""
        loads = self.food
        # gold: every 100 gp *or fraction thereof* counts as one load
        if self.gold > 0:
            loads += (self.gold + 99) // 100
        return loads

    def max_capacity(self):
        """r206b - calculate the total load capacity of the whole party."""
        cap = 0
        for c in self.living():
            if hasattr(c, '_carried') and c._carried:
                # An unconscious Prince being carried contributes 0 capacity
                continue
            if c.mount != 'none':
                # Mounted character: mount can carry 30 loads;
                # the rider counts as 20 loads of that, leaving 10 for cargo.
                cap += 10
            else:
                # On foot: 10 loads each
                cap += 10
        return cap

    def loads_used(self):
        """Return (used, capacity) for status display."""
        used = self.current_loads()
        cap = self.max_capacity()
        return used, cap

    def check_loads(self):
        """r206 - enforce load limits.  If the party is over-capacity, prompt
        the player to leave excess items behind or cache them."""
        used = self.current_loads()
        cap = self.max_capacity()
        if used <= cap:
            return 'Loads within capacity.'
        excess = used - cap
        self.note(f'Over capacity by {excess} load(s) (r206: {used}/{cap}).')
        # Try to auto-cache excess gold if possible; each 100 gold cached
        # removes one load, but each individual food unit removed also helps.
        # For now we just log the warning; the player must cache voluntarily
        # before picking another action, or we auto-reduce.
        return self.prompt_load_reduction(excess)

    def prompt_load_reduction(self, excess):
        """Prompt the player to drop or cache excess loads."""
        self.push('choice', 'Over capacity (r206)',
                  f'The party is carrying {self.current_loads()} loads but '
                  f'can only carry {self.max_capacity()}. '
                  f'{excess} load(s) must be left behind.',
                  [{'label': 'Cache excess gold (auto)',
                    'handler': (lambda: self._auto_cache_loads(excess))},
                   {'label': 'Accept and continue (load penalty)',
                    'handler': (lambda: 'Accepting load penalty.')}])
        return 'Over capacity - decision pending.'

    def _auto_cache_loads(self, excess):
        """Cache enough gold to bring the party within load capacity."""
        cached = 0
        while excess > 0 and self.gold >= 100:
            # Cache in increments of 100 gold (= 1 load each)
            self.cache(100)
            cached += 100
            excess -= 1
        # If still over and we have remaining gold < 100, cache the rest too
        if excess > 0 and self.gold > 0:
            self.cache(self.gold)
            cached += self.gold
        self.note(f'Cached {cached} gold to reduce loads.')
        return 'Loads reduced.'


    # ------------------------------------------------------------ travel (r204, r205)
    def is_road_move(self, a, b):
        return frozenset((a, b)) in self.road_sides

    def is_river_move(self, a, b):
        return frozenset((a, b)) in self.river_sides

    def raft_available(self):
        """r213 - rafting needs the river: the hex must touch a river hexside.

        Once the party is afloat it stays on the raft until it gets off (by
        choosing any other daily action) or the raft is lost or dismantled.
        """
        if self.raft:
            return True
        return any(self.is_river_move(self.hex, hid)
                   for hid in self.model.neighbors(self.hex).values())

    def check_lost(self, terrain):
        """r205 - roll 2 dice vs the terrain threshold; a guide subtracts 1.

        r205a: if the party is lost anyway, roll one die - on a 4 or more the
        guide deserts, mortified by the failure.
        """
        row = self.model.travel_row(terrain)
        thr = threshold(row['lost']) if row else None
        if thr is None:
            return False
        guide = next((c for c in self.living() if c.guide), None)
        r = self.d2() - (1 if guide else 0)
        lost = r >= thr
        self.note(f'Getting lost check [{terrain}]: rolled {r} vs {thr}+ '
                  + ('-> LOST' if lost else '-> ok'))
        if lost and guide is not None:
            die = self.d1()
            self.note(f'The guide failed: die {die} (a 4+ and he leaves, r205a).')
            if die >= 4:
                guide.alive = False
                self.party = [c for c in self.party if c.alive]
                self.note(f'{guide.name} deserts out of shame (r205a).')
        return lost

    def travel_event(self, hid, road=False, flying=False, rafting=False):
        terrain = ('Rafting' if rafting else 'On Road' if road
                   else 'Airborne' if flying
                   else self.model.travel_terrain(hid))
        row = self.model.travel_row(terrain)
        if not row:
            return
        thr = threshold(row['event_threshold'])
        r = self.d2()
        if thr is not None and r >= thr:
            die = self.d1()
            ref = row['event_refs'][die - 1]
            code = self.model.resolve_event_ref(ref, die)
            self.note(f'Travel event [{terrain}]: rolled {r} (needs {thr}+), '
                      f'die {die} -> {ref} -> {code}')
            self.encounter(code)
            if self.event_kind in (None, 'other', 'combat'):
                if self.moves_left > 0:
                    self.moves_left = 0
                    self.note('The encounter takes the rest of the day (r204f).')
        else:
            self.note(f'No travel event [{terrain}]: rolled {r} (needs {thr}+).')

    def begin_travel(self):
        """r204a - start the day's travel, choosing air or ground if winged."""
        if self.speed() == 3:
            self.push('choice', 'Winged mounts (r204a)',
                      'The whole party is on winged mounts: fly for the whole '
                      'day (three hexes, airborne events), or short-hop on the '
                      'ground (two hexes, like ordinary mounts)?',
                      [{'label': 'Fly (3 hexes, airborne)',
                        'handler': (lambda: self.start_travel(3, True))},
                       {'label': 'Short-hop (2 hexes, on the ground)',
                        'handler': (lambda: self.start_travel(2, False))}])
            return 'Choose how to travel.'
        self.start_travel(self.speed(), False)
        return 'Travelling.'

    def start_travel(self, moves, flying):
        # r205d: a party left "over the river" keeps that state into tomorrow,
        # so it is *not* cleared here; entering the far bank clears it.
        self.action = 'travel'
        self.moves_left = moves
        self.flying = flying
        self.note(f'Travel action: the party moves {moves} hex/day '
                  + ('(airborne)' if flying else
                     '(mounted)' if moves == 2 else '(on foot)'))
        self.choose_move()
        return 'Travelling.'

    def begin_raft(self):
        """r213 - take to the raft and travel along the river hexsides.

        The raft covers three hexsides a day going downriver but only two
        going up, so the day's allowance is fixed by the first move (the water
        runs top to bottom on the map).  The party is only offered river sides;
        getting lost is impossible on the water (r205b).
        """
        if not self.raft and not self.raft_available():
            self.note('No raft here - the party is nowhere near a river (r213).')
            return 'No raft available.'
        self.raft = True
        self.action = 'raft'
        self.raft_dir = None
        self.moves_left = RAFT_SPEED
        self.note('The party takes to the raft (r213).')
        self.choose_move()
        return 'Rafting.'

    def river_name(self, src, dest):
        """Which r213 river this hexside belongs to ('' if not a river)."""
        return (self.river_names.get(f'{src}|{dest}')
                or self.river_names.get(f'{dest}|{src}')
                or '')

    def raft_direction(self, src, dest):
        """Is this river move downriver or upriver? (r213)"""
        downstream = self.river_flow.get(f'{src}|{dest}')
        if downstream is None:                   # no data: fall back to the row
            downstream = dest if int(dest[2:]) > int(src[2:]) else src
        return 'down' if downstream == dest else 'up'

    def raft_stop_check(self):
        """r213 - after a day on the raft, a roll of 12 reaches a stop."""
        roll = self.d2()
        if roll == 12:
            self.raft = False
            self.note('The raft reaches a stopping point and is dismantled '
                      '(r213).')
        else:
            self.note(f'The raft travels on (stop check {roll}, only a 12 stops '
                      f'it - r213).')

    def choose_move(self):
        nbs = self.model.neighbors(self.hex)
        opts = []
        for d, hid in sorted(nbs.items()):
            if self.raft and not self.is_river_move(self.hex, hid):
                continue                     # a raft follows the river
            label = f'{d} -> {hid} ({self.model.travel_terrain(hid)})'
            if self.is_road_move(self.hex, hid):
                label += ' [road]'
            if self.is_river_move(self.hex, hid):
                label += ' [river]'
            opts.append({'label': label,
                         'handler': (lambda hid=hid: self.move(hid))})
        if self.raft and not opts:
            self.note('The river does not continue from this hex (r213).')
            self.moves_left = 0
            self.raft_stop_check()
            return self.stop_travel()
        opts.append({'label': 'Stop travelling for the day',
                     'handler': (lambda: self.stop_travel())})
        self.push('choice', f'Move ({self.moves_left} hex(es) left)',
                  f'In hex {self.hex}. Choose the next hex to enter (r204).', opts)

    def stop_travel(self):
        self.moves_left = 0
        self.note('The party stops travelling for the day.')
        return 'Travel ended.'

    def move(self, dest):
        src = self.hex
        if self.moves_left <= 0:
            self.note('No movement left this day.')
            return False
        if dest not in self.model.neighbors(src).values():
            self.note(f'{dest} is not adjacent to {src}.')
            return False
        if self.raft:
            # r213: on the water the party follows river hexsides and can
            # never get lost (r205b); the travel event is read under "Rafting".
            if not self.is_river_move(src, dest):
                self.note('A raft can only follow the river (r213).')
                return False
            if self.raft_dir is None:
                # r213: three hexsides a day downriver, two upriver - the
                # first move of the day settles which it is.
                self.raft_dir = self.raft_direction(src, dest)
                self.moves_left = (RAFT_SPEED if self.raft_dir == 'down'
                                   else RAFT_UPSTREAM)
                self.note(f'The raft sets off {self.raft_dir}river: '
                          f'{self.moves_left} hexsides today (r213).')
            self.hex = dest
            self.moves_left -= 1
            self.visited.add(dest)
            self.note(f'Raft {src} -> {dest} (r213).')
            self.travel_event(dest, rafting=True)
            if self.moves_left <= 0:
                self.raft_stop_check()
            return True
        road = self.is_road_move(src, dest)
        river = self.is_river_move(src, dest)
        self.note(f'Travel {src} -> {dest}: {self.model.travel_terrain(src)} -> '
                  f'{self.model.travel_terrain(dest)}'
                  + (' [road]' if road else '') + (' [river]' if river else ''))
        # r205: getting lost is checked for every hex entered, using the terrain
        # of the hex the party is leaving (roads are exempt).
        crossed = False
        river_name = self.river_name(src, dest)
        if not road and river and not self.flying:
            # r205d: first the crossing itself, on the "Cross River" line.
            if (src, river_name) in self.crossed:
                self.note(f'The party is already over the {river_name} here '
                          f'(r205d).')
            elif self.check_lost('Cross River'):
                self.moves_left = 0
                self.note('No crossing found - the day is spent on the bank '
                          '(r205d). No travel event.')
                return False
            else:
                crossed = True
        if not road:
            if crossed:
                # ... then the ordinary check for entering the far hex.
                lost = self.check_lost(self.model.travel_terrain(dest))
            else:
                lost = self.check_lost('Airborne' if self.flying
                                       else self.model.travel_terrain(src))
            if lost:
                self.moves_left = 0
                if crossed:
                    # "You count as across the river, but are still in the hex
                    # where you started the move" - tomorrow any hex on the far
                    # bank of this river can be entered from here (r205d).
                    self.crossed.add((src, river_name))
                    far = [h for h in self.model.neighbors(src).values()
                           if self.is_river_move(src, h)
                           and self.river_name(src, h) == river_name]
                    self.note(f'Across the {river_name} but lost on the far '
                              f'side: the party stays in {src}; tomorrow '
                              f'{", ".join(sorted(far))} can be entered '
                              f'without crossing again (r205d). No travel '
                              f'event.')
                    return False
                if self.flying:
                    if self.d1() >= 4:
                        d = self.d1()
                        drift = self.model.neighbors(src).get(DIRECTIONS[d - 1])
                        if drift:
                            self.hex = drift
                            self.visited.add(drift)
                            self.note(f'Airborne and lost: blown to {drift} (r205c).')
                else:
                    self.note('Lost - the day is spent wandering in ' + src + ', '
                              'checking the hex that was entered (r205b).')
                self.travel_event(dest, road=road, flying=self.flying)
                return False

        self.hex = dest
        if river and not road:
            # the far bank is reached: the r205d carry-over is spent
            self.crossed.discard((src, river_name))
        self.moves_left -= 1
        self.visited.add(dest)
        self.travel_event(dest, road=road, flying=self.flying)
        return True


    # ------------------------------------------------------------ prompt plumbing
    def push(self, kind, title, text, options):
        self.prompts.append({'kind': kind, 'title': title, 'text': text,
                             'options': options})

    def current(self):
        return self.prompts[0] if self.prompts else None

    def answer(self, index=0):
        p = self.prompts.pop(0)
        opt = p['options'][index]
        return opt['handler']()

    def is_busy(self):
        return bool(self.prompts)

    def advance(self):
        """Move the day state machine forward until a prompt is available."""
        while not self.prompts:
            if self.game_over:
                return None
            if self.combat:
                self.push_combat()
                continue
            if self.imprisoned:
                self.prison_step()
                continue
            if self.phase == 'action':
                if self.action is None:
                    self.daily_menu()
                elif self.action == 'travel' and self.moves_left > 0:
                    self.choose_move()
                elif self.action == 'raft' and self.moves_left > 0:
                    self.choose_move()
                else:
                    if self.action == 'raft':
                        self.raft_stop_check()
                    self.phase = 'endday'
                    self.food_done = False
                    self.end_day()
            elif self.phase == 'endday':
                if not self.food_done:
                    self.food_done = True
                    self.lodging()
                else:
                    self.finish_day()
                    self.phase = 'action'
        return self.current()



    # ------------------------------------------------------------ encounters (r207)
    def encounter(self, code):
        ev = self.model.events.get(code)
        if not ev:
            self.note(f'(event {code} is not in the booklet - nothing happens)')
            return
        if code == 'e050':
            # e050: the constabulary only acts within three hexes of a town,
            # castle or temple, and Ogon/Weshor send e002 instead.
            place, dist = self.constabulary()
            if place is None or dist > 3:
                self.note('The local constabulary is too far away to act '
                          '(e050) - nothing happens.')
                return
            if place in ('0101', '1501'):
                self.note(f'Constabulary from {place} - see e002 instead (e050).')
                code = 'e002'
                ev = self.model.events.get(code) or ev
        if code in ('e060', 'e061', 'e062', 'e063'):
            self.enter_prison(code)
            return
        if code == 'e044':
            # The High Altar's die table is written with ". " separators, which
            # the generic parser cannot read, so it is resolved by hand.
            return self.high_altar()
        # A chain of booklet cross-references can loop back on itself (e130
        # audience notes).  Refuse to re-enter an event already on the queue.
        chain = {p.get('code') for p in self.prompts if p.get('code')}
        if code in chain:
            self.note(f'(event {code} repeats itself - nothing further happens)')
            return
        self.event_kind = 'other'
        opts = parse_options(ev['text'])
        self.pending_event = {'code': code, 'title': ev['title'], 'text': ev['text'],
                              'headers': [], 'rows': [], 'note': '', 'setup': None}
        if opts:
            headers, rows, note = opts
            self.pending_event.update({'headers': headers, 'rows': rows, 'note': note})
            self.pending_event['setup'] = self.event_setup(ev)
            self.push('encounter', f'{code} - {ev["title"]}',
                      ev['text'] + ('\n' + note if note else ''),
                      self.option_choices(headers))
            self.prompts[-1]['code'] = code
        else:
            entries = die_entries(ev['text'])
            if entries:
                return self.roll_die_table(entries, ev)
            m = GOLD_TEXT_RE.search(ev['text'])
            if m:
                self.gold += int(m.group(1))
                self.note(f'Gain {m.group(1)} gold from {ev["title"]}.')
            self.push('info', f'{code} - {ev["title"]}', ev['text'],
                      [{'label': 'Continue', 'handler': (lambda: 'Continuing.')}])
            self.prompts[-1]['code'] = code

    def event_setup(self, ev):
        """Resolve the 'roll one die for ...' table that precedes the options.

        e130 rolls the identity of the lord before the option matrix, and the
        audience footnote later depends on who that lord turned out to be.
        """
        m = re.search(r'options are', ev['text'], re.I)
        head = ev['text'][:m.start()] if m else ev['text']
        entries = die_entries(head)
        if not entries:
            return None
        die = self.d1()
        entry = next((text for rolls, text in entries if die in rolls), None)
        if entry is None:
            return None
        self.note(f'{ev["title"]}: die {die} - {entry}')
        return entry


    def roll_die_table(self, entries, ev):
        """Resolve a "roll one die: 1-x; 2-y; ..." table inside an event."""
        die = self.d1()
        entry = next((text for rolls, text in entries if die in rolls), None)
        if entry is None:
            self.note(f'{ev["title"]}: die {die} has no entry - nothing happens.')
            return 'Nothing happens.'
        m = REF_RE.search(entry)
        if m and m.group(1) in self.model.index:
            self.note(f'{ev["title"]}: die {die} -> {m.group(1)}')
            return self.resolve_ref(m.group(1), ev)
        gm = re.search(r'wealth\s+(\d+)', entry, re.I) or \
            re.search(r'(\d+)\s*gold', entry, re.I)
        if gm:
            amount = int(gm.group(1))
            self.gold += amount
            self.note(f'{ev["title"]}: die {die} - {entry} (gain {amount} gold).')
            return f'Gain {amount} gold.'
        self.note(f'{ev["title"]}: die {die} - {entry}')
        return 'Nothing happens.'

    def altar_blessing(self):
        """e044 roll 6: a god appears at the High Altar and pledges support.

        The Prince must give all his money to the gods instantly, his endurance
        is permanently reduced by one (-1), and he wins the game if he returns
        alive to any hex north of the Tragoth River within the next 30 days
        (checked in ``finish_day``).
        """
        self.gold = 0
        p = self.prince()
        if p:
            p.endurance -= 1
        self.altar_blessed_day = self.day
        self.note('A god appears at the High Altar and pledges support to your '
                  'cause (e044).')
        self.note('You give all your money to the gods, and your endurance is '
                  f'permanently reduced by one ({p.endurance if p else "?"}).')
        if self.north_of_tragoth():
            self.note('You are already north of the Tragoth River - the '
                      'blessing wins the game the moment the day ends.')
        else:
            self.note('You must return alive to a hex north of the Tragoth '
                      f'River within {self.ALTAR_BLESSING_DAYS} days to win.')

    def high_altar(self):
        """e044 - the High Altar: a priest or monk in the party can invoke it.

        Only a priest or monk knows the invocations; without one the event ends.
        Roll one die: 1 the invoker dies; 2 the altar collapses and the party is
        wounded; 3 the invoker is wounded and the altar is the wrong god's; 4 an
        impossible riddle ends invocations; 5 a prophecy (see e147); 6 a god
        pledges support and the Prince must reach the Northlands within 30 days
        (the winning blessing, see ``altar_blessing``).
        """
        party = self.living()
        invoker = next((c for c in party
                        if any(k in c.name.lower()
                               for k in ('priest', 'monk'))), None)
        if invoker is None:
            self.note('No priest or monk is in the party to invoke the High '
                      'Altar - the event ends (e044).')
            return 'No invocation.'
        die = self.d1()
        self.note(f'High Altar invocation by {invoker.name}: die {die} (e044).')
        if die == 1:
            invoker.alive = False
            self.note(f'{invoker.name} is engulfed in godly fires and dies.')
        elif die == 2:
            self.note('Lightning and earthquakes destroy the High Altar.')
            for c in self.living():
                c.wounds += die
                self.note(f'{c.name} is wounded ({c.wounds}/{c.endurance})'
                          + (' -> dead' if c.dead else ''))
                if c.dead:
                    c.alive = False
            self.party = [c for c in self.party if c.alive]
            if not self.living():
                self.game_over = True
                self.reason = 'The party was destroyed at the High Altar (e044).'
        elif die == 3:
            invoker.wounds += 1
            self.note(f'{invoker.name} is struck for one wound '
                      f'({invoker.wounds}/{invoker.endurance}); the altar is the '
                      'wrong god and further invocations are impossible.')
        elif die == 4:
            self.note('A voice of the gods gives an impossible riddle and a '
                      'prophecy none can understand - no more invocations.')
        elif die == 5:
            self.note('The gods give a prophecy that seems to promise a '
                      'treasure (e147).')
            self.encounter('e147')
        else:
            self.altar_blessing()
        return 'The High Altar is invoked.'


    def evade_override(self, ev, header):
        """A footnote may replace the evade die roll with a free escape.

        e003 roll 6: 'if your party has wing mounts ... you may use escape
        mounted r312 instead of rolling the die' - the mounted escape is free,
        no die is rolled.  Flying escapes need a winged mount for everyone.
        """
        if header.lower() != 'evade':
            return None
        note = ev.get('note') or ''
        low = note.lower()
        if 'instead of rolling' not in low and 'instead of a die' not in low:
            return None
        party = self.living()
        if not party:
            return None
        if 'not in forest' in low and self.model.terrain(self.hex) == 'forest':
            return None
        flying = re.search(r'escape flying\s*\(?([rc]\d{3})', low)
        mounted = re.search(r'escape mounted\s*\(?([rc]\d{3})', low)
        if flying and all(c.mount == 'winged' for c in party):
            return normalise_ref(flying.group(1))
        if mounted and any(c.mount != 'none' for c in party):
            return normalise_ref(mounted.group(1))
        return None

    def constabulary(self):
        """(hex, distance) of the nearest town, castle or temple (e050)."""
        best, dist = None, 9999
        for hid, place in self.features.get('places', {}).items():
            if place.get('kind') not in ('town', 'castle', 'temple'):
                continue
            d = self.model.distance(self.hex, hid)
            if d is not None and d < dist:
                best, dist = hid, d
        return best, dist

    def option_bonus(self, ev):
        """Footnote bonuses to the option die: mounts (+1), forest (+2), e050.

        The booklet states the bonus explicitly, e.g. e002 'if your entire
        party has mounts, add one (+1) to die roll' and e007 'if the event
        occurs in a forest, add two (+2) to the die roll'.

        e050 adds +2 when the nearest town/castle/temple has been visited
        before (unless the party left it by an escape) and +1 when it has
        never been visited at all.
        """
        note = ev.get('note') or ''
        party = self.living()
        bonus = int(ev.get('bonus', 0))
        if ev.get('code') == 'e050':
            place, _dist = self.constabulary()
            if place:
                if place in self.visited and place not in self.escaped_from:
                    bonus += 2
                    self.note(f'The nearest place, {place}, has been visited '
                              f'before (+2, e050).')
                elif place not in self.visited:
                    bonus += 1
                    self.note(f'Never visited {place} before (+1, e050).')
        for clause in re.split(r'[;,]', note):
            low = clause.lower()
            if 'add one (+1)' in low:
                if party and any(c.mount != 'none' for c in party):
                    if 'entire party' in low or 'all ' in low:
                        if all(c.mount != 'none' for c in party):
                            bonus += 1
                    else:
                        bonus += 1
            elif 'add two (+2)' in low:
                if self.model.terrain(self.hex) == 'forest':
                    bonus += 2
        return bonus

    def option_choices(self, headers):
        return [{'label': f'{h} (roll one die)',
                 'handler': (lambda i=i: self.roll_option(i))}
                for i, h in enumerate(headers)]

    def roll_option(self, header_index):
        ev = self.pending_event
        header = ev['headers'][header_index]
        override = self.evade_override(ev, header)
        if override:
            self.note(f'{header}: {override} used instead of a die roll.')
            return self.resolve_ref(override, ev)
        die = self.d1()
        bonus = self.option_bonus(ev)
        roll = die + bonus
        rolls = [r for r, _ in ev['rows']]
        limit = max(rolls) if rolls else 6
        m = re.search(r'higher than (\d+)', ev.get('note') or '', re.I)
        if m:
            limit = min(limit, int(m.group(1)))
        if roll > limit:
            self.note(f'Option die {die} + {bonus} = {roll}, treated as {limit}.')
            roll = limit
        row = next((cells for r, cells in ev['rows'] if r == roll), None)
        if not row:
            self.note(f'No entry for a roll of {roll}.')
            return 'Nothing happens.'
        label, ref = row[header_index] if header_index < len(row) else row[-1]
        self.note(f'{header} - die {die}' + (f' + {bonus}' if bonus else '')
                 + f' = {roll}: {label}')
        if ref is None:
            return self.resolve_label(label, ev, header_index)
        return self.resolve_ref(ref, ev, label)

    def resolve_label(self, label, ev, header_index):
        """An option cell with no reference: 'roll again', 'audience', etc."""
        low = label.lower()
        if 'roll again' in low:
            ev['rerolls'] = ev.get('rerolls', 0) + 1
            if ev['rerolls'] >= 3:
                self.note('Rolling again produces nothing further; the encounter ends.')
                return 'The encounter ends.'
            self.note('Roll again.')
            return self.roll_option(header_index)
        if 'audience' in low:
            return self.lord_audience(ev)
        self.note(f'{label}: nothing further happens.')
        return 'The encounter ends.'

    def lord_audience(self, ev):
        """e130: the lord grants an audience, whose outcome is footnoted."""
        lord = ev.get('setup') or 'the lord'
        note = ev.get('note') or ''
        clauses = note.split(';')
        table = []
        for k, clause in enumerate(clauses):
            m = re.search(r'roll one die:\s*(.+)', clause, re.I)
            if m:
                table.append(m.group(1))
                for nxt in clauses[k + 1:]:
                    if re.match(r'\s*\d+(?:,\s*\d+)*\s*-', nxt):
                        table.append(nxt)
                    else:
                        break
                break
        die = self.d1()
        for chunk in table:
            d = re.match(r'\s*(\d+(?:,\s*\d+)*)\s*-\s*(.+)', chunk)
            if d and die in [int(x) for x in d.group(1).split(',')]:
                outcome = d.group(2).strip()
                ref = REF_RE.search(outcome)
                if ref:
                    self.note(f'Audience with {lord}: die {die} -> {ref.group(1)}')
                    return self.resolve_ref(ref.group(1), ev)
                self.note(f'Audience with {lord}: die {die} - {outcome}')
                return 'The audience ends.'
        clause = next((c for c in clauses
                       if lord.split()[0].lower() in c.lower()), '')
        ref = REF_RE.search(clause)
        if ref:
            self.note(f'Audience with {lord} -> {ref.group(1)}')
            return self.resolve_ref(ref.group(1), ev)
        self.note(f'Audience with {lord}: nothing comes of it.')
        return 'The audience ends.'

    def re_encounter(self):
        """Return to the event and pick another option (r314, r317, ...)."""
        ev = self.pending_event
        if not ev or not ev.get('headers'):
            return 'The encounter ends.'
        ev['attempts'] = ev.get('attempts', 0) + 1
        if ev['attempts'] >= 3:
            self.note('Three attempts at this encounter have failed; it ends.')
            self.pending_event = None
            return 'The encounter ends.'
        self.push('choice', f'{ev["code"]} - {ev["title"]} (try again)',
                  'That option failed. Choose another approach.',
                  self.option_choices(ev['headers']))
        return 'Choose another option.'


    # ------------------------------------------------------------ combat (r220)
    def battle_situation(self, ref):
        """r300-r310: who strikes first, and who has surprise."""
        die = self.d1()
        if ref == 'r300':
            self.note(f'{ref}: your party surprises them.')
            return True, 'party'
        if ref == 'r301':
            s = 'party' if self.wit >= die else None
            self.note(f'{ref}: die {die}, wit {self.wit} '
                      + ('-> surprise' if s else '-> you strike first'))
            return True, s
        if ref == 'r302':
            s = 'party' if self.wit > die else None
            self.note(f'{ref}: die {die}, wit {self.wit} '
                      + ('-> surprise' if s else '-> you strike first'))
            return True, s
        if ref == 'r303':
            s = 'party' if len(self.living()) < die else None
            self.note(f'{ref}: die {die}, party {len(self.living())} '
                      + ('-> surprise' if s else '-> you strike first'))
            return True, s
        if ref == 'r304':
            self.note(f'{ref}: your party strikes first.')
            return True, None
        if ref == 'r305':
            first = self.wit >= die
            self.note(f'{ref}: die {die}, wit {self.wit} '
                      + ('-> you strike first' if first else '-> they strike first'))
            return first, None
        if ref == 'r306':
            first = self.wit > die
            self.note(f'{ref}: die {die}, wit {self.wit} '
                      + ('-> you strike first' if first else '-> they strike first'))
            return first, None
        if ref == 'r307':
            self.note(f'{ref}: they strike first.')
            return False, None
        if ref == 'r308':
            s = None if self.wit >= die else 'foes'
            self.note(f'{ref}: die {die}, wit {self.wit} '
                      + ('-> you sense danger' if s is None else '-> they surprise you'))
            return False, s
        if ref == 'r309':
            s = None if self.wit > die else 'foes'
            self.note(f'{ref}: die {die}, wit {self.wit} '
                      + ('-> you sense danger' if s is None else '-> they surprise you'))
            return False, s
        self.note(f'{ref}: they surprise your party.')
        return False, 'foes'

    def start_combat(self, ev=None, modifier=0):
        self.event_kind = 'combat'
        total = self.d2() + modifier
        ref = BATTLE_REFERENCE.get(min(12, max(2, total)), 'r306')
        self.note(f'Battle reference: rolled {total} -> {ref}')
        first, surprise = self.battle_situation(ref)
        foes = parse_foes(ev['text'] if ev else '', self.rng)
        if not foes:
            foes = [Character('Foe 1', 4, 5, 0)]
        self.combat = Combat(self.living(), foes, self.rng, first,
                             (ev['title'] if ev else 'Battle'), surprise, self.note)
        self.note(f'Combat: party ({len(self.combat.party)}) vs '
                  f'foes ({len(self.combat.foes)})')
        self.push_combat()
        return 'Combat begins.'

    def push_combat(self):
        c = self.combat
        body = '\n'.join(c.log[-12:])
        body += '\nParty: ' + ', '.join(repr(x) for x in c.party)
        body += '\nFoes:  ' + ', '.join(repr(x) for x in c.foes)
        self.push('combat', f'Combat - {c.name} (round {c.round})', body,
                  [{'label': 'Fight this round', 'handler': (lambda: self.fight_round())},
                   {'label': 'Attempt to escape (r220e)',
                    'handler': (lambda: self.flee_combat())}])

    def fight_round(self):
        self.combat.step()
        if self.combat.over:
            return self.finish_combat()
        self.push_combat()
        return 'Combat continues.'

    def flee_combat(self):
        ok, die = self.combat.attempt_escape()
        if ok:
            self.note('The party breaks off and escapes the battle.')
            self.combat = None
            self.escape_move()
            return 'Escaped from combat.'
        self.push_combat()
        return 'Escape fails.'

    def finish_combat(self):
        c = self.combat
        self.note(f'Combat ends: {c.result}.')
        if c.result in ('party wins', 'foes routed'):
            self.event_kind = 'combat_won'
            self.note('The fight is over - the party can travel on (r204f).')
        if c.result in ('party wins', 'foes routed'):
            # r225: "Whenever you kill all characters encountered, your party
            # may take their wealth" - the defeated band, not whoever is still
            # standing, is what gets looted.
            for foe in c.original_foes:
                gold, item, event = self.treasure_roll(foe.wealth)
                self.gain_treasure(gold, item, event)
                self.note(f'Loot from {foe.name}: {gold} gold'
                          + (f' + {item}' if item else ''))
        self.combat = None
        self.party = [x for x in self.party if x.alive]
        # r221c: if the Prince is dead, the game is lost immediately.
        p = self.prince()
        if p and p.dead:
            self.game_over = True
            self.reason = ('The Barbarian Prince has been killed in combat. '
                           'Game over!')
            return f'Combat over - the Prince is dead ({c.result}).'
        # r221b: if the Prince is unconscious (wounds == endurance - 1),
        # roll 1d6 for follower attitude.
        if p and p.unconscious and not p.dead:
            followers = [c for c in self.living() if not c.prince]
            if followers:
                die = self.d1()
                self.note(f'The Prince is unconscious (r221b) - follower roll: {die}.')
                if die >= 4:
                    self.note('Followers carry the unconscious Prince (r221b). '
                              'He counts as 20 loads.')
                    # The prince is carried -- transport rules apply;
                    # his effective capacity drops to 0 (he can carry nothing).
                    p._carried = True
                else:
                    self.note('Followers desert the unconscious Prince '
                              'with all money and possessions (r221b).')
                    self.gold = 0
                    self.items = []
                    self.staff = False
                    self.helm = False
                    for f in followers:
                        f.alive = False
                        self.note(f'{f.name} deserts.')
                    self.party = [x for x in self.party if x.alive]
        if not self.living():
            self.game_over = True
            self.reason = 'The whole party has been wiped out.'
        return f'Combat over ({c.result}).'


    # ------------------------------------------------------------ escape & hide (r218)
    def escape_move(self):
        """Move randomly to an adjacent hex; rivers and off-map are re-rolled."""
        origin = self.hex
        for _ in range(12):
            d = self.rng.choice(DIRECTIONS)
            hid = self.model.neighbors(self.hex).get(d)
            if hid is None:
                self.note('Escape direction leads off the map - roll again.')
                continue
            if self.is_river_move(self.hex, hid) and not self.flying:
                self.note('Escape across a river is prohibited - roll again.')
                continue
            self.hex = hid
            self.visited.add(hid)
            if origin in self.features.get('places', {}):
                # e050: leaving a town by an escape makes the party "wanted"
                self.escaped_from.add(origin)
            self.note(f'Escaped to hex {hid} ({self.model.travel_terrain(hid)}).')
            return hid
        self.note('No escape route available - the party stays put.')
        return self.hex

    def hide_here(self):
        self.note('The party hides in this hex for the rest of the day.')
        self.moves_left = 0
        self.action = 'hide'
        return 'Hiding.'

    def escape_ref(self, ref, ev):
        if ref == 'r311':
            self.escape_move()
            return 'Escaped.'
        if ref == 'r312':
            if all(c.mount != 'none' for c in self.living()):
                self.escape_move()
                return 'Escaped mounted.'
            opts = [{'label': 'Abandon the unmounted and ride away',
                     'handler': (lambda: self.abandon_unmounted())},
                    {'label': 'Stand and fight (r330)',
                     'handler': (lambda: self.start_combat(ev))}]
            self.push('choice', 'Escape mounted (r312)',
                      'Not everyone in the party has a mount.', opts)
            return 'Decide what to do.'
        if ref == 'r313':
            if all(c.mount == 'winged' for c in self.living()):
                self.escape_move()
                return 'Escaped by flight.'
            opts = [{'label': 'Abandon those who cannot fly',
                     'handler': (lambda: self.abandon_unmounted())},
                    {'label': 'Stand and fight (r330)',
                     'handler': (lambda: self.start_combat(ev))}]
            self.push('choice', 'Escape flying (r313)',
                      'Not everyone in the party can fly.', opts)
            return 'Decide what to do.'
        die = self.d1()
        if (ref == 'r314' and self.wit >= die) or (ref == 'r315' and self.wit > die):
            self.note(f'Talking escape: die {die}, wit {self.wit} -> it works.')
            self.escape_move()
            return 'Escaped.'
        self.note(f'Talking escape: die {die}, wit {self.wit} -> it fails.')
        return self.re_encounter()

    def abandon_unmounted(self):
        left = [c for c in self.living() if c.mount == 'none' and not c.prince]
        for c in left:
            self.note(f'{c.name} is abandoned.')
            c.alive = False
        self.party = [c for c in self.party if c.alive]
        self.escape_move()
        return 'Escaped, leaving the unmounted behind.'

    def hide_ref(self, ref, ev):
        if ref == 'r316':
            return self.hide_here()
        die = self.d1()
        if ref == 'r317' and self.wit >= die:
            return self.hide_here()
        if ref == 'r318' and self.wit > die:
            return self.hide_here()
        if ref == 'r319' and len(self.living()) <= die:
            return self.hide_here()
        if ref == 'r320' and len(self.living()) < die:
            return self.hide_here()
        self.note(f'Hiding attempt fails (die {die}).')
        return self.re_encounter()

    # ------------------------------------------------------------ bribe & pass (r321-r329)
    def bribe_amount(self, ev, label=''):
        """The bribe is stated in the option cell, e.g. 'bribe (10)'."""
        m = re.search(r'\((\d+)\)', label)
        if m:
            return int(m.group(1))
        if not ev:
            return 10
        m = re.search(r'(\d+)\s*(?:gold|gp)', ev['text'])
        return int(m.group(1)) if m else 10

    def bribe_ref(self, ref, ev, label=''):
        amount = self.bribe_amount(ev, label)
        if self.gold < amount:
            self.note(f'You cannot afford the {amount} gold bribe.')
            if ref == 'r324':
                return self.forced_battle(ev, 0, foes_first=True)
            mod = 1 if ref == 'r321' else (-1 if ref == 'r323' else 0)
            return self.forced_battle(ev, mod)
        self.gold -= amount
        self.note(f'Bribed them {amount} gold - the encounter ends.')
        return 'Passed by.'


    def forced_battle(self, ev, modifier=0, foes_first=False):
        if foes_first:
            self.combat = Combat(self.living(), parse_foes(ev['text'] if ev else ''),
                                 self.rng, False, (ev['title'] if ev else 'Battle'),
                                 'foes', self.note)
            self.push_combat()
            return 'Combat begins.'
        return self.start_combat(ev, modifier)

    def pass_ref(self, ref, ev):
        if ref == 'r325':
            self.note('They lose interest and let you pass.')
            return 'Passed by.'
        die = self.d1()
        ok = (ref in ('r326', 'r327') and self.wit >= die) or \
             (ref in ('r328', 'r329') and self.wit > die)
        if ok:
            self.note(f'Talk your way past: die {die}, wit {self.wit} -> they let you pass.')
            return 'Passed by.'
        mod = 1 if ref in ('r326',) else (-1 if ref == 'r329' else 0)
        self.note(f'Talking fails (die {die}, wit {self.wit}) - forced to fight.')
        return self.forced_battle(ev, mod)


    # ------------------------------------------------------------ hiring (r331-r340)
    def offer_hire(self, ev, pay, bonus=0, unreliable=False, town_leaver=False,
                    on_refuse=None):
        foes = parse_foes(ev['text'] if ev else '')
        if not foes:
            return 'Nobody to hire.'
        opts = [{'label': f'Hire all {len(foes)} for {pay} gold/day'
                          + (f' (+{bonus} bonus now)' if bonus else ''),
                 'handler': (lambda: self.accept_hire(foes, pay, unreliable,
                                                      town_leaver))}]
        opts.append({'label': 'Refuse',
                     'handler': on_refuse or (lambda: 'They pass by.')})
        self.push('choice', 'Hiring (r331-r340)',
                  f'{len(foes)} character(s) offer to join: '
                  + ', '.join(repr(f) for f in foes), opts)
        return 'Decide whether to hire.'

    def accept_hire(self, foes, pay, unreliable=False, town_leaver=False):
        bonus = pay * len(foes)
        if bonus and self.gold < bonus:
            self.note('You cannot pay today\'s wages - they refuse.')
            return 'Hiring fails.'
        self.gold -= bonus
        ev = self.pending_event or {}
        calling = self.calling(ev.get('title', '') + ' ' + ev.get('text', ''))
        for f in foes:
            f.pay = pay
            f.unreliable = unreliable
            f.town_leaver = town_leaver
            f.name = f.name.replace('Foe', 'Hired')
            if calling:
                f.kind = calling
        self.party.extend(foes)
        self.note(f'{len(foes)} character(s) join the party at {pay} gold/day each.')
        return 'Followers acquired.'

    @staticmethod
    def calling(text):
        """'magician' or 'priest' if the text describes one, else ''."""
        low = text.lower()
        if any(w in low for w in ('wizard', 'magician', 'witch', 'sorcerer')):
            return 'magician'
        if any(w in low for w in ('priest', 'priestess', 'monk', 'acolyte')):
            return 'priest'
        return ''

    def refuse_roll(self, ev, mapping):
        die = self.d1()
        ref = mapping.get(die, 'r325')
        self.note(f'Refusal roll {die} -> {ref}')
        return self.resolve_ref(ref, ev)

    def hire_ref(self, ref, ev, label=''):
        amount = self.bribe_amount(ev, label)
        if ref == 'r331':
            if self.gold >= amount:
                self.gold -= amount
                return self.accept_hire(parse_foes(ev['text']), 0, unreliable=True)
            die = self.d1()
            if die <= 3:
                self.note('They ignore you - the encounter ends.')
                return 'They ignore you.'
            return self.bribe_ref({4: 'r321', 5: 'r322', 6: 'r323'}[die], ev)
        if ref == 'r332':
            return self.offer_hire(ev, 2, bonus=amount,
                                  on_refuse=lambda: self.refuse_roll(
                                      ev, {3: 'r321', 4: 'r322', 5: 'r323', 6: 'r324'}))
        if ref == 'r333':
            return self.offer_hire(ev, 2)
        if ref == 'r334':
            return self.accept_hire(parse_foes(ev['text']), 0)
        if ref == 'r335':
            return self.accept_hire(parse_foes(ev['text']), 0, town_leaver=True)
        if ref == 'r336':
            die = self.d1()
            if self.wit >= die:
                return self.accept_hire(parse_foes(ev['text']), 0)
            self.note('They decline - the encounter ends.')
            return 'They leave.'
        if ref == 'r337':
            die = self.d1()
            if self.wit > die:
                return self.accept_hire(parse_foes(ev['text']), 0)
            die = self.d1()
            if die == 1:
                return 'They pass by.'
            if die == 2:
                return self.forced_battle(ev)
            if die == 3:
                return self.hire_ref('r340', ev)
            if die <= 5:
                return self.conversation(ev)
            return self.general_inquiry(ev)
        return 'Nothing happens.'


    def hire_ref2(self, ref, ev):
        if ref == 'r338':
            die = self.d1()
            if self.wit >= die:
                pay = 1 if self.wit > die else 2
                return self.accept_hire(parse_foes(ev['text']), pay)
            self.note('You fail to convince them - they pass by.')
            return 'They pass by.'
        if ref == 'r339':
            die = self.d1()
            if self.wit > die:
                return self.accept_hire(parse_foes(ev['text']), 2)
            die = self.d1()
            return ('They pass by.' if die <= 3 else self.forced_battle(ev))
        if ref == 'r340':
            opts = [{'label': 'Let them pass', 'handler': (lambda: 'They pass by.')},
                    {'label': 'Try to convince them to join',
                     'handler': (lambda: self.looter(ev))}]
            self.push('choice', 'Looters (r340)', 'Let them pass or convince them?', opts)
            return 'Decide.'
        return 'Nothing happens.'

    def looter(self, ev):
        die = self.d1()
        if self.wit >= die:
            return self.accept_hire(parse_foes(ev['text']), 0, unreliable=True)
        die = self.d1()
        if die <= 2:
            self.note('They attack you personally, striking first.')
            self.combat = Combat(self.living(), parse_foes(ev['text']), self.rng,
                                 False, ev['title'], 'foes', self.note)
            self.push_combat()
            return 'Combat.'
        if die <= 4:
            return self.forced_battle(ev)
        self.note('They depart angry, without fighting.')
        return 'They leave.'

    # ------------------------------------------------------------ conversation (r341, r342)
    def conversation(self, ev):
        self.event_kind = 'other'     # r341: the talk takes the rest of the day
        self.note('Conversation (r341) takes the whole day - no further travel.')
        self.moves_left = 0
        self.action = 'conversation'
        total = self.d2()
        ref = CONVERSATION.get(total, 'r325')
        self.note(f'Conversation roll {total} -> {ref}')
        if ref == 'r310':
            self.combat = Combat(self.living(), parse_foes(ev['text']), self.rng,
                                 False, ev['title'], 'foes', self.note)
            self.push_combat()
            return 'Combat.'
        if ref in ('r308', 'r305'):
            return self.start_combat(ev)
        return self.resolve_ref(ref, ev)

    def general_inquiry(self, ev):
        total = self.d2()
        ref = INQUIRY.get(total, 'r325')
        self.note(f'General inquiry roll {total} -> {ref}')
        if ref == 'r330':
            return self.forced_battle(ev)
        if ref in ('r309', 'r306'):
            return self.start_combat(ev)
        return self.resolve_ref(ref, ev)

    def victim_selection(self, ev):
        """r343 - randomly select a party member as the victim."""
        party = self.living()
        for _ in range(12):
            c = self.rng.choice(party)
            if self.d1() == 6 or len(party) == 1:
                self.note(f'The victim selected is {c.name}.')
                return c
        self.note(f'The victim selected is {party[0].name}.')
        return party[0]

    # ------------------------------------------------------------ reference resolver
    def resolve_ref(self, ref, ev=None, label=''):
        if ref in ('r325', 'r326', 'r327', 'r328', 'r342'):
            # a brief word does not end the day (r204f); r341 conversation
            # explicitly does, and sets its own state
            self.event_kind = 'talk'
        if not ref:
            return 'Nothing happens.'
        ref = self.model.index.get('reference_fixes', {}).get(ref, ref)
        if ref.startswith('e'):
            # an event reference: the encounter continues in that booklet entry
            self.encounter(ref)
            title = self.model.events.get(ref, {}).get('title', ref)
            return f'The encounter continues at {ref} - {title}.'
        if ref in ('r300', 'r301', 'r302', 'r303', 'r304', 'r305', 'r306',
                   'r307', 'r308', 'r309', 'r310'):
            return self.start_combat(ev)
        if ref in ('r311', 'r312', 'r313', 'r314', 'r315'):
            return self.escape_ref(ref, ev)
        if ref in ('r316', 'r317', 'r318', 'r319', 'r320'):
            return self.hide_ref(ref, ev)
        if ref in ('r321', 'r322', 'r323', 'r324'):
            return self.bribe_ref(ref, ev, label)
        if ref in ('r325', 'r326', 'r327', 'r328', 'r329'):
            return self.pass_ref(ref, ev)
        if ref == 'r330':
            return self.forced_battle(ev)
        if ref in ('r331', 'r332', 'r333', 'r334', 'r335', 'r336', 'r337'):
            return self.hire_ref(ref, ev, label)
        if ref in ('r338', 'r339', 'r340'):
            return self.hire_ref2(ref, ev)
        if ref == 'r341':
            return self.conversation(ev)
        if ref == 'r342':
            return self.general_inquiry(ev)
        if ref == 'r343':
            self.victim_selection(ev)
            return self.forced_battle(ev)
        self.note(f'(reference {ref} is not implemented - nothing happens)')
        return 'Nothing happens.'


    # ------------------------------------------------------------ daily actions
    def begin_action(self, action):
        self.action = action
        if action != 'raft' and self.raft:
            self.note('The party leaves the raft (r213).')
            self.raft = False
        if action == 'travel':
            return self.begin_travel()
        if action == 'rest':
            return self.rest()
        if action == 'news':
            return self.seek_news()
        if action == 'hire':
            return self.seek_hire()
        if action == 'audience':
            return self.seek_audience()
        if action == 'offerings':
            return self.make_offerings()
        if action == 'ruins':
            return self.search_ruins()
        if action == 'cache':
            return self.recover_cache()
        if action == 'raft':
            return self.begin_raft()
        if action == 'follow':
            return self.do_follow()
        if action == 'explore':
            return self.explore()
        return 'Unknown action.'

    def seek_news(self):
        """r209 - seek news: 2 dice, +1 for spending 5+ gold, +1 if wit is 5+."""
        spend = 5 if self.gold >= 5 else 0
        if spend:
            self.gold -= spend
        bonus = (1 if spend else 0) + (1 if self.wit >= 5 else 0)
        total = self.d2() + bonus
        self.note(f'Seeking news: rolled {total} (bonus {bonus}).')
        row = self.model.news(total)
        text = row['text'] if row else 'No news of note, nothing seems to be happening.'
        self.note(f'News roll {total} -> {text}')
        low = text.lower()
        if 'gain 50 gold' in low:
            self.gold += 50
        elif 'lose half your wealth' in low:
            self.gold //= 2
        if 'add one (+1)' in low and 'offerings' in low:
            self.offering_bonus = 1
        if 'always add one (+1)' in low:
            self.news_bonus[self.hex] = 1
        if 'half normal price' in low:
            self.news_bonus[self.hex] = 2
        m = REF_RE.search(text)
        if m and m.group(1) in self.model.events:
            self.encounter(m.group(1))
        else:
            self.push('info', f'News in {self.hex}', text,
                      [{'label': 'Continue', 'handler': (lambda: 'Continuing.')}])
        return 'News gathered.'

    def search_ruins(self):
        """r208 - search the ruins: roll two dice on the ruins table."""
        dice = self.d2()
        code = RUINS.get(min(12, max(2, dice)), 'e133')
        self.note(f'Searching the ruins: rolled {dice} -> {code} (r208).')
        # r208 result 8 is e132 "Organized Search": alone the day is wasted;
        # with a party, roll one die and only a roll below the party size lets
        # the search continue immediately.
        if code == 'e132' and len(self.living()) > 1 and self._ruins_retry < 40:
            die = self.d1()
            if die < len(self.living()):
                self._ruins_retry += 1
                self.note(f'Organised search: die {die} < party '
                          f'{len(self.living())} - search again today (e132).')
                return self.search_ruins()
            self.note(f'Organised search: die {die} - the party finds nothing '
                      f'more today (e132).')
            self._ruins_retry = 0
            return 'Ruins searched.'
        self._ruins_retry = 0
        self.encounter(code)
        return 'Ruins searched.'

    def recover_cache(self):
        """r214 - find the cache again: 1-4 intact, 5 not found, 6 looted."""
        if self.hex not in self.caches:
            self.note('There is no cache hidden in this hex.')
            return 'No cache here.'
        _code, amount = self.caches[self.hex]
        die = self.d1()
        self.note(f'Searching for the cache: die {die} (r214).')
        if die <= 4:
            self.caches.pop(self.hex)
            self.gain_treasure(amount, None, None)
            self.note(f'The cache is found intact: {amount} gold recovered.')
            return 'Cache recovered.'
        if die == 5:
            self.note('The cache cannot be found - landmarks have gone, but it '
                      'may be searched for again (r214).')
            return 'Cache not found.'
        self.caches.pop(self.hex)
        self.note('The cache is found, but it has been looted (r214).')
        return 'Cache looted.'

    def raft_action(self):
        """r213 - raft down the river: 2 dice, +1 per follower with skill 6+."""
        if not self.raft_available():
            self.note('No raft here - the party is nowhere near a river (r213).')
            return 'No raft available.'
        self.raft = True
        bonus = sum(1 for c in self.living() if c.skill >= 6)
        total = self.d2() + bonus
        self.note(f'Rafting: rolled {total} (bonus {bonus}).')
        if total <= 10:
            self.note('The raft is lost and the day is wasted.')
            self.raft = False
            return 'Raft lost.'
        code = RAFTING.get(total, 'r232')
        if code.startswith('r'):
            code = self.model.resolve_event_ref(code, self.d1())
        self.note(f'Rafting roll {total} -> {code}')
        self.raft_days += 1
        if total >= 12:
            self.raft = False
            self.note('The raft reaches a stopping point and is dismantled.')
        self.encounter(code)
        return 'Rafting continues.'

    def audience_rows(self):
        """The r211 audience table that applies to the hex we are standing in."""
        table = self.model.tables['audience']
        for entry in table.values():
            if entry.get('hex') == self.hex:
                return entry['rows']
        kind = self.place_kind(self.hex)
        return table.get('any Town' if kind in ('town', 'castle')
                         else 'any Temple', {}).get('rows', [])

    def party_kinds(self):
        """(has priest/monk, has magician/wizard/witch) among the followers.

        A follower's calling comes from the event that recruited them; the name
        is only a fallback, because recruits join as "Hired 1" and the like.
        """
        followers = [c for c in self.living() if not c.prince]
        priests = ('priest', 'priestess', 'monk', 'acolyte')
        magicians = ('magician', 'wizard', 'witch', 'sorcerer')

        def kind_of(c):
            if getattr(c, 'kind', ''):
                return c.kind
            low = c.name.lower()
            if any(w in low for w in magicians):
                return 'magician'
            if any(w in low for w in priests):
                return 'priest'
            return ''

        kinds = {kind_of(c) for c in followers}
        return 'priest' in kinds, 'magician' in kinds

    def seek_audience(self):
        """r211 - seek an audience: 2 dice on the local table.

        At a temple the party's composition matters: priests and monks add one
        (+1), while magicians, wizards and witches subtract two (-2) unless
        they are dismissed first.

        At Huldra Castle (1212) the Baron will take a wizard, magician or witch
        into his own service, which adds one (+1) to the audience roll.
        """
        kind = self.place_kind(self.hex)
        if kind not in ('town', 'castle', 'temple'):
            self.note('There is nobody here to grant an audience.')
            return 'No audience available.'
        bonus = 0
        if kind == 'temple':
            has_priest, has_magic = self.party_kinds()
            if has_priest:
                bonus += 1
            if has_magic:
                bonus -= 2
                self.note('A magician in the party is unwelcome here (-2, r211).')
            if bonus:
                self.note(f'Temple audience modifier {bonus:+d} (r211).')
        if self.hex == '1212':
            wizard = next((c for c in self.living()
                           if not c.prince and c.kind == 'magician'), None)
            if wizard is not None:
                self.push(
                    'choice', 'Audience at Huldra Castle (r211)',
                    f'{wizard.name} could take service with the Baron instead '
                    f'of staying in the party, which adds one (+1) to the '
                    f'audience roll.',
                    [{'label': f'Dismiss {wizard.name} to the Baron (+1)',
                      'handler': (lambda w=wizard, b=bonus:
                                  self.baron_dismiss(w, b))},
                     {'label': 'Keep the party as it is',
                      'handler': (lambda b=bonus: self.audience_roll(b))}])
                return 'Audience decision pending.'
        return self.audience_roll(bonus)

    def baron_dismiss(self, who, bonus):
        """r211 - give a wizard to the Baron of Huldra for +1 on the roll."""
        self.dismiss(who)
        self.note(f'{who.name} enters the Baron\'s service (+1, r211).')
        return self.audience_roll(bonus + 1)

    def dismiss(self, who):
        """r201 - voluntarily dismiss a follower from the party."""
        if who is None or getattr(who, 'prince', False):
            return False
        if who in self.party:
            self.party.remove(who)
            self.note(f'{who.name} is dismissed from the party (r201).')
            return True
        return False

    def audience_roll(self, bonus):
        """Roll the local audience table with `bonus` added."""
        kind = self.place_kind(self.hex)
        total = self.d2() + bonus
        self.note(f'Seeking an audience in {kind} {self.hex}: rolled {total}.')
        row = self.model.roll_row(self.audience_rows(), total)
        text = (row['text'] if row else 'The audience is refused - try again tomorrow.')
        self.note(f'Audience roll {total} -> {text}')
        m = REF_RE.search(text)
        if m and m.group(1) in self.model.events:
            self.encounter(m.group(1))
        else:
            self.push('info', f'Audience in {kind} {self.hex}', text,
                      [{'label': 'Continue', 'handler': (lambda: 'Continuing.')}])
        return 'Audience sought.'

    def make_offerings(self):
        """r212 - submit offerings at a temple."""
        kind = self.place_kind(self.hex)
        if kind != 'temple':
            self.note('There is nowhere here to make offerings.')
            return 'No offerings possible.'
        opts = [{'label': f'Offer {g} gold',
                 'handler': (lambda g=g: self.offering(g))}
                for g in (1, 5, 10, 20, 50) if g <= self.gold]
        if not opts:
            self.note('You have no gold to offer.')
            return 'No offerings.'
        opts.append({'label': 'Withdraw', 'handler': (lambda: 'Offerings abandoned.')})
        self.push('choice', 'Submit offerings (r212)',
                  f'How much gold do you offer at the temple in {self.hex}? '
                  f'Spending 10 or more adds one (+1) to the roll.', opts)
        return 'Choose an offering.'

    def offering(self, amount):
        """r212 - 2 dice, +1 for 10+ gold; 14+ wins the Staff of Command.

        Modifiers: +1 for the 10-gold sacrifice, +1 for the permanent omen
        won by seeking news (r209 result 4), +1 for favourable omens from the
        previous offering (r212 result 7, "again tomorrow" only) and +3 for
        the High Priest's influence (r212 result 12/13, tomorrow only).
        """
        self.gold -= amount
        bonus = ((1 if amount >= 10 else 0) + self.offering_bonus
                 + self.omen_bonus + self.influence_bonus)
        dice = self.d2()
        total = dice + bonus
        self.note(f'Offering of {amount} gold: dice {dice} + {bonus} = {total} '
                  f'(r212).')
        # Both one-day modifiers are spent by this attempt.
        self.omen_bonus = 0
        self.influence_bonus = 0
        row = self.model.offerings(total)
        text = row['text'] if row else 'Nothing happens.'
        low = text.lower()
        if 'staff of command' in low:
            self.staff = True
            self.note('The Staff of Command is in your hands.')
            self.note('A pair of warrior monks (skill 5, endurance 6, mounted) '
                      'join you to help carry the Staff north of the Tragoth '
                      '(r212).')
            self.party.append(Character('Warrior Monk', 5, 6, mount='horse'))
            self.party.append(Character('Warrior Monk', 5, 6, mount='horse'))
            if self.north_of_tragoth():
                self.note('You are already north of the Tragoth River.')
            else:
                self.note('You must carry the Staff to a hex north of the '
                          'Tragoth River to win (r212).')
        if 'free food' in low or 'free lodging' in low:
            self.free_lodging = True
        if total == 7:
            self.omen_bonus = 1
            self.note('Favourable omens: +1 to the offering roll tomorrow.')
        if total in (12, 13) and not self.staff:
            return self.high_priest_offer(text)
        m = REF_RE.search(text)
        if m and m.group(1) in self.model.events:
            self.encounter(m.group(1))
        else:
            self.push('info', f'Offerings at {self.hex}', text,
                      [{'label': 'Continue', 'handler': (lambda: 'Continuing.')}])
        return 'Offerings made.'

    def high_priest_offer(self, text):
        """r212 result 12/13 - secret information or the Priest's influence."""
        self.note('The High Priest offers either his clues or his influence.')
        self.push('choice', 'The High Priest\'s offer (r212)',
                  'The High Priest can either give you the final clues to his '
                  'secret information, or use his influence so that you add '
                  'three (+3) to your dice roll if you make Offerings here '
                  'again tomorrow.',
                  [{'label': 'Take the secret information',
                    'handler': (lambda: self.priest_clues())},
                   {'label': 'Use his influence (+3 tomorrow)',
                    'handler': (lambda: self.priest_influence())}])
        return 'The High Priest makes an offer.'

    def priest_clues(self):
        die = self.d1()
        ref = ('e144', 'e144', 'e145', 'e145', 'e146', 'e146')[die - 1]
        self.note(f'High Priest\'s clues (die {die}) -> {ref}')
        self.encounter(ref)
        return 'Secret information received.'

    def priest_influence(self):
        self.influence_bonus = 3
        self.note('The High Priest will back your offering: add three (+3) '
                'to the roll tomorrow (r212).')
        return 'Influence accepted.'


    # ------------------------------------------------------------ rest (r222)
    def rest(self):
        self.note('Resting in hex ' + self.hex + ' (r222).')
        self.moves_left = 0
        self.action = 'rest'
        before = len(self.log)
        self.travel_event(self.hex, road=self.is_road_move(self.hex, self.hex))
        events = self.log[before:]
        combat_or_escape = any('combat' in e.lower() or 'escape' in e.lower()
                               or 'rout' in e.lower() for e in events)
        if self.prompts:
            return 'Rest interrupted by an encounter.'
        for c in self.living():
            # r222: a poisoned wound never heals with rest, so the poisoned
            # count is a floor on the wounds left behind.
            if c.wounds > c.poisoned:
                c.wounds -= 1
                self.note(f'{c.name} heals a wound ({c.wounds}/{c.endurance}).')
        if combat_or_escape:
            self.note('The rest was disturbed, so no wounds are healed.')
        return 'Rested and healed.'

    # ------------------------------------------------------------ trap locks (r227)
    def do_trap_lock(self, victim=None):
        """r227 - open or enter an item with a trap lock.

        If ``victim`` is None the Prince opens it himself.  Roll one die for
        the trap outcome and inflict wounds accordingly.
        """
        p = victim or self.prince()
        if p is None:
            self.note('No one available to open the trap lock.')
            return 'No victim.'
        die = self.d1()
        self.note(f'{p.name} attempts to open a trap lock - roll {die} (r227).')
        if die == 1:
            # Poison needle: 1 poisoned wound
            p.wounds += 1
            p.poisoned += 1
            self.note(f'{p.name} is struck by a poison needle: 1 poisoned wound '\
                      f'({p.wounds}/{p.endurance}).')
        elif die == 2:
            # Burning acid: roll d6 wounds
            wounds = self.d1()
            p.wounds += wounds
            self.note(f'{p.name} is hit by burning acid: {wounds} wounds '\
                      f'({p.wounds}/{p.endurance}).')
        elif die == 3:
            # Poison gas: roll d6 poison wounds
            wounds = self.d1()
            p.wounds += wounds
            p.poisoned += wounds
            self.note(f'{p.name} is engulfed by poison gas: {wounds} poison wounds '\
                      f'({p.wounds}/{p.endurance}).')
        elif die == 4:
            # Plague dust: sickness, d6 halved (round up) wounds each day
            base = (self.d1() + 1) // 2
            p.wounds += base
            self.note(f'{p.name} is contaminated by plague dust: {base} sickness '\
                      f'wounds at end of each day ({p.wounds}/{p.endurance}). '\
                      'Recovery check needed.')
            # Recovery check
            rec = self.d1()
            if rec >= 4:
                self.note(f'Recovery roll {rec} - {p.name} recovers from the sickness.')
                p._sickness = 0
            else:
                p._sickness = base
                self.note(f'Recovery roll {rec} - sickness continues for {p.name} '\
                          f'({base} wounds/day).')
        elif die == 5:
            # Flying spikes: d6 + 3 wounds
            wounds = self.d1() + 3
            p.wounds += wounds
            self.note(f'{p.name} is blasted by flying spikes: {wounds} wounds '\
                      f'({p.wounds}/{p.endurance}).')
        else:
            # die == 6: trap malfunctions
            self.note(f'{p.name} triggers the lock but the trap malfunctions - '\
                      'no damage.')
        # Check for death
        if p.dead:
            p.alive = False
            self.note(f'{p.name} has died from trap wounds.')
            if p.prince:
                self.game_over = True
                self.reason = ('The Barbarian Prince has died from a trap lock. '\
                               'Game over!')
        return f'Trap lock resolved ({die}).'

    # ------------------------------------------------------------ following (r219)
    def do_follow(self):
        """r219 - follow or trail encountered characters.

        Rolls 1d6 for the direction the chase leads, moves the party to that
        hex, and ends all remaining normal travel/actions for the day.
        """
        self.note('Following encountered characters (r219).')
        direction = self.d1()
        d = DIRECTIONS[direction - 1]
        dest = self.model.neighbors(self.hex).get(d)
        if dest is None:
            self.note(f'Cannot follow in direction {d} - no hex in that direction.')
            return 'Follow failed.'
        self.hex = dest
        self.visited.add(dest)
        self.moves_left = 0
        self.note(f'Rolled {direction} -> following toward {d}, '\
                  f'arriving at hex {dest}. All other actions end.')
        return f'Following to {dest}.'


    # ------------------------------------------------------------ food (r215, r216)
    def foraging_ok(self):
        t = self.model.terrain(self.hex)
        return t in ('farmland', 'countryside', 'forest', 'hills')

    def meal_gold(self):
        """r215d - a bought meal is 1 gold a character, 1 gold a mount.

        (Animals are fed at the stable for one gold a day, or stabled with two
        food units each - see `food_need`, which is the *unit* price.)
        """
        return len(self.living()) + sum(1 for c in self.living()
                                        if c.mount != 'none')

    def food_need(self):
        need = len(self.living())
        if not self.foraging_ok():
            need += 2 * sum(1 for c in self.living() if c.mount != 'none')
        if self.model.terrain(self.hex) == 'desert':
            need *= 2
        return need

    def buy_food(self):
        """r215e - buy food stores, 1 gold a unit, in a settled hex.

        Only what the party can carry is offered, and spending the day at the
        market is the day's action.
        """
        kind = self.place_kind(self.hex)
        if kind not in ('town', 'castle', 'village', 'temple'):
            self.note('There is no market here (r215e).')
            return 'No market.'
        room = max(0, self.max_capacity() - self.current_loads())
        afford = min(self.gold, room)
        opts = []
        for n in (1, 3, 5, 10):
            if n <= afford:
                opts.append({'label': f'Buy {n} unit(s) for {n} gold',
                             'handler': (lambda n=n: self.buy_food_units(n))})
        opts.append({'label': 'Buy nothing',
                     'handler': (lambda: 'Nothing bought.')})
        self.push('choice', 'Buy food stores (r215e)',
                  f'Stores cost 1 gold a unit. You have {self.gold} gold and '
                  f'room for {room} more load(s) of food.', opts)
        return 'Market open.'

    def buy_food_units(self, units):
        """r215e - pay for and carry `units` of food, spending the day."""
        units = max(0, min(units, self.gold,
                           self.max_capacity() - self.current_loads()))
        if not units:
            self.note('Nothing was bought.')
            return 'Nothing bought.'
        self.gold -= units
        self.food += units
        self.moves_left = 0
        self.note(f'Bought {units} food unit(s) for {units} gold; '
                  f'{self.food} in stores (r215e).')
        return 'Food bought.'

    def feed_party(self):
        need = self.food_need()
        kind = self.place_kind(self.hex)
        opts = []
        if self.food >= need:
            opts.append({'label': f'Eat from stores ({need} units)',
                         'handler': (lambda: self.eat_stores(need))})
        if self.food >= 2 * need:
            opts.append({'label': f'Eat a double meal ({2 * need} units, '
                                  f'undoes two days of starvation)',
                         'handler': (lambda: self.eat_stores(need, 2))})
        if kind in ('town', 'castle', 'temple'):
            gold = self.meal_gold()
            opts.append({'label': f'Buy meals ({gold} gold)',
                         'handler': (lambda: self.buy_meals(gold, 1, gold))})
            if self.gold >= 2 * gold:
                opts.append({'label': f'Buy a double meal ({2 * gold} gold, '
                                      f'undoes two days of starvation)',
                             'handler': (lambda: self.buy_meals(gold, 2,
                                                                2 * gold))})
        if not (kind in ('town', 'castle', 'temple')):
            if self.action == 'hide':
                # r218b: hiding means no hunting (mounts may still forage)
                self.note('The party is hiding; hunting is impossible (r218b).')
            else:
                opts.append({'label': 'Go hunting (r215b)',
                             'handler': (lambda: self.hunt(need))})
        opts.append({'label': 'Go hungry (r216)',
                     'handler': (lambda: self.starve(need))})
        self.push('choice', f'Evening meal - need {need} food units',
                  f'Party needs {need} food units; you have {self.food} in stores.',
                  opts)

    def feed_effect(self, portions=1):
        """Apply r216b's recovery to everyone who eats."""
        for c in self.living():
            if c.starved:
                before = c.starved
                c.feed(portions)
                if c.starved != before:
                    self.note(f'{c.name} eats and recovers '
                              f'({c.effective_skill} skill, '
                              f'{c.load_capacity()} loads).')

    def eat_stores(self, need, portions=1):
        self.food -= need * portions
        self.note(f'Ate {need * portions} food units from stores'
                  + (' (a double meal)' if portions > 1 else '') + '.')
        self.feed_effect(portions)
        return 'Fed.'

    def buy_meals(self, need, portions=1, cost=None):
        cost = cost if cost is not None else need * portions
        if self.gold >= cost:
            self.gold -= cost
            self.note(f'Bought meals for {cost} gold'
                      + (' (a double meal)' if portions > 1 else '') + '.')
            self.feed_effect(portions)
            return 'Fed.'
        self.note('Not enough gold to buy meals.')
        return self.starve(need)

    def hunt(self, need):
        living = self.living()
        hunter = max(living, key=lambda c: c.skill + c.remaining // 2)
        total = hunter.skill + hunter.remaining // 2
        # r215b: a hunter who can act as a guide adds one, and after a day of
        # rest the rest of the party may join - each extra hunter adds one,
        # and each extra hunter who is a guide adds one more.
        if hunter.guide:
            total += 1
        if self.action == 'rest':
            extras = [c for c in living if c is not hunter]
            if extras:
                total += len(extras) + sum(1 for c in extras if c.guide)
                self.note(f'{len(extras)} extra hunter(s) join the hunt after '
                          f'the rest day (r215b).')
        dice = self.d2()
        gained = total - dice
        self.note(f'Hunting by {hunter.name}: {total} - {dice} = {gained} units.')
        if dice == 12:
            wounds = self.d1()
            hunter.wounds += wounds
            self.note(f'The hunter is hurt: {wounds} wounds '
                      f'({hunter.wounds}/{hunter.endurance})'
                      + (' -> dead' if hunter.dead else ''))
            if hunter.dead or hunter.unconscious:
                gained = 0
                if hunter.dead and len(living) == 1:
                    hunter.alive = False
        if self.model.terrain(self.hex) == 'farmland':
            # r215c: hunting in farmland risks an event after the hunt -
            # 1-4 nothing, 5 peasant mob (e017), 6 constabulary (e050), and
            # the hunt is what gets the party reported: +2 on that die roll.
            die = self.d1()
            self.note(f'Farmland hunt: event die {die} (r215c).')
            if die == 5:
                self.note('Peasant mob in pursuit (e017).')
                self.encounter('e017')
            elif die == 6:
                self.note('Pursued by constabulary (e050).')
                self.encounter('e050')
                if self.pending_event and self.pending_event.get('code') in ('e050', 'e002'):
                    self.pending_event['bonus'] = \
                        self.pending_event.get('bonus', 0) + 2
                    self.note('The hunt is reported: add two (+2) to the '
                              'constabulary die (r215c).')
        if gained > 0:
            self.food += gained
            self.note(f'Hunt yields {gained} food units.')
        # The evening meal is eaten out of tonight's catch (or the stores it
        # tops up): what is left over is what gets banked, and only a real
        # shortfall causes starvation.
        if self.food >= need:
            self.food -= need
            self.note(f'Ate {need} food units; {self.food} kept in stores.')
            # r216b: eating undoes a day of starvation, two for a double meal
            self.feed_effect(2 if self.food >= need else 1)
        else:
            short = need - self.food
            self.food = 0
            self.note(f'Still short {short} unit(s) - some go hungry.')
            self.starve(short)
        return 'Hunted.'

    def starve(self, shortfall):
        self.note(f'{shortfall} food unit(s) short - starvation (r216).')
        for c in self.living():
            if c.prince:
                # r216b: the Prince cannot desert, but he still goes hungry -
                # his loads halve and his combat skill drops by one per day.
                c.starved += 1
                self.note(f'The Prince starves (skill now {c.effective_skill}, '
                          f'loads {c.load_capacity()}).')
                continue
            die = self.d2() - self.wit
            if die >= 4:
                self.note(f'{c.name} deserts because of hunger.')
                c.alive = False
            else:
                c.starved += 1
                self.note(f'{c.name} starves (skill now {c.effective_skill}).')
        self.party = [c for c in self.party if c.alive]
        if not self.living():
            self.game_over = True
            self.reason = 'The whole party deserted or died.'
        return 'Starvation resolved.'


    # ------------------------------------------------------------ hiring (r210)
    def seek_hire(self):
        kind = self.place_kind(self.hex)
        if kind not in ('town', 'castle'):
            self.note('You can only seek to hire followers in a town or castle.')
            return 'No hiring possible here.'
        bonus = 1 if self.news_bonus.get(self.hex) else 0
        total = self.d2() + bonus
        row = self.model.roll_row(self.model.tables['hiring'], total)
        text = row['text'] if row else 'Nothing available.'
        self.note(f'Seeking to hire: rolled {total} -> {text}')
        m = re.search(r'e(\d{3})', text)
        if m:
            self.encounter('e' + m.group(1))
            return 'Hiring attempt led to an encounter.'
        if total == 2:
            return self.offer_hire({'text': 'Freeman (skill 3, endurance 4)'}, 0)
        if total == 3:
            return self.offer_hire({'text': 'Lancer (skill 5, endurance 5, horse)'},
                                   3)
        if total == 4:
            n = self.d1()
            n = min(2, max(1, n - 4))
            return self.offer_hire({'text': f'Mercenary x{n} (skill 4, endurance 4)'}, 2)
        if total in (5, 10):
            price = 10 if total == 5 else 7
            opts = [{'label': f'Buy {i} horse(s) for {i * price} gold',
                     'handler': (lambda i=i: self.buy_horses(i, price))}
                    for i in (1, 2, 3) if i * price <= self.gold]
            opts.append({'label': 'Decline', 'handler': (lambda: 'No horses bought.')})
            self.push('choice', 'Horse dealer', f'Horses cost {price} gold each.', opts)
            return 'Horse dealer offers.'
        if total == 6:
            return self.offer_hire({'text': 'Local guide (skill 2, endurance 3)'}, 2)
        if total == 7:
            n = self.d1()
            return self.offer_hire({'text': f'Henchmen x{n} (skill 3, endurance 3)'}, 1)
        if total == 11:
            return self.offer_hire({'text': 'Runaway (skill 1, endurance 3)'}, 0)
        if total >= 12:
            opts = [{'label': 'Hire a porter (1 gold/day)',
                     'handler': (lambda: self.accept_hire(
                         [Character('Porter', 1, 3, 0)], 1))},
                    {'label': 'Hire a guide (2 gold/day, skill 1, endurance 2)',
                     'handler': (lambda: self.accept_hire(
                         [Character('Guide', 1, 2, 0, guide=True)], 2))},
                    {'label': 'Decline', 'handler': (lambda: 'Nobody hired.')}]
            self.push('choice', 'Porters & guides available', 'Who do you hire?', opts)
            return 'Hiring options.'
        return 'Nothing available.'

    def buy_horses(self, n, price):
        if self.gold < n * price:
            self.note('Not enough gold for horses.')
            return 'No horses bought.'
        self.gold -= n * price
        for c in self.living():
            if c.mount == 'none':
                c.mount = 'horse'
                n -= 1
                if n == 0:
                    break
        self.note('Bought horses; party now mounted.')
        return 'Horses bought.'

    # ------------------------------------------------------------ lodging (r217)
    def lodging(self):
        kind = self.place_kind(self.hex)
        if kind not in ('town', 'castle', 'temple'):
            return 'Camp for the night in the open.'
        # r217: the Prince needs his own room, as does any priest, monk,
        # magician, wizard or witch; every other follower shares, two a room.
        followers = [c for c in self.living() if not c.prince]
        special = sum(1 for c in followers
                      if any(w in c.name.lower() for w in
                             ('priest', 'monk', 'magician', 'wizard', 'witch')))
        others = len(followers) - special
        rooms = 1 + special + (others + 1) // 2
        mounts = sum(1 for c in self.living() if c.mount != 'none')
        cost = rooms + mounts
        if self.free_lodging:
            self.free_lodging = False
            self.note('Lodging is provided free of charge.')
            return 'Free lodging.'
        opts = [{'label': f'Pay {cost} gold for lodging',
                 'handler': (lambda: self.pay_lodging(cost))},
                {'label': 'Sleep rough (risk desertion)',
                 'handler': (lambda: self.sleep_rough())}]
        self.push('choice', f'Lodging in {kind} {self.hex} (r217)',
                  f'{rooms} room(s) + {mounts} stable(s) = {cost} gold.', opts)
        return 'Lodging decision pending.'

    def pay_lodging(self, cost):
        if self.gold >= cost:
            self.gold -= cost
            self.note(f'Paid {cost} gold for lodging.')
            return 'Lodged.'
        self.note('Cannot afford lodging.')
        return self.sleep_rough()

    def sleep_rough(self):
        self.note('No lodging purchased - rolling for desertion (r217).')
        for c in list(self.living()):
            if c.prince:
                # r217: the Prince does not desert his own quest, but a mount
                # left without a stable can still be stolen overnight.
                if c.mount != 'none' and self.d1() >= 4:
                    self.note('The Prince\'s mount is stolen during the night '
                              '(r217).')
                    c.mount = 'none'
                continue
            die = self.d2() - self.wit
            if die >= 4:
                self.note(f'{c.name} deserts - no lodging provided.')
                c.alive = False
            else:
                self.note(f'{c.name} stays ({die}).')
            if c.mount != 'none':
                if self.d1() >= 4:
                    self.note(f'{c.name}\'s mount is stolen during the night.')
                    c.mount = 'none'
        self.party = [c for c in self.party if c.alive]
        if not self.living():
            self.game_over = True
            self.reason = 'The party deserted.'
        return 'Slept rough.'


    # ------------------------------------------------------------ end of day
    def skip_day(self):
        self.note('The party does nothing today.')
        self.action = 'skip'
        return 'Day passed.'

    def end_day(self):
        if self.combat:
            self.note('A battle is still in progress - the day cannot end.')
            return 'Day not finished.'
        self.feed_party()
        return 'End-of-day routines started.'

    def sickness_step(self):
        """r227 - plague dust keeps biting each evening until it is shaken."""
        for c in self.living():
            n = getattr(c, '_sickness', 0)
            if not n:
                continue
            c.wounds += n
            self.note(f'{c.name} suffers {n} sickness wound(s) '
                      f'({c.wounds}/{c.endurance}) - plague dust (r227).')
            rec = self.d1()
            if rec >= 4:
                c._sickness = 0
                self.note(f'Recovery roll {rec}: the sickness passes (r227).')
            else:
                self.note(f'Recovery roll {rec}: the sickness continues '
                          f'({n} a day, r227).')
            if c.dead and c.prince:
                self.game_over = True
                self.reason = 'The Prince dies of the trap\'s plague (r227).'

    def finish_day(self):
        """Called after food/lodging prompts are answered."""
        self.peak_gold = max(self.peak_gold, self.gold)
        self.sickness_step()
        self.action = None
        self.pending_event = None
        self.event_kind = None      # r204f: 'talk' / 'combat' allow travelling on
        # r205d: (hex, river) pairs the party has already crossed - from those
        # hexes the far bank can be entered without another crossing check
        self.crossed = set()
        # --- altar-blessing victory must be checked BEFORE the day increments ---
        # so that a blessing received on day N still counts day N + 30 as valid
        # (e.g., blessed on day 5, reach north on day 35: 35-5 = 30 ≤ 30 ✓)
        if (self.altar_blessed_day is not None
                and self.north_of_tragoth()
                and self.day - self.altar_blessed_day
                <= self.ALTAR_BLESSING_DAYS):
            self.game_over = True
            self.won = True
            self.reason = ('You return alive to the Northlands within 30 days '
                           'of the High Altar blessing - the gods strike down '
                           'the usurpers and you regain your throne. Victory!')
        # --- advance to the next day for all remaining checks ---
        self.day += 1
        if self.staff and self.north_of_tragoth():
            self.game_over = True
            self.won = True
            self.reason = ('The Staff of Command is carried north of the '
                           'Tragoth River - you command the Northlands and '
                           'regain your throne. Victory!')
        elif self.helm and self.hex in self.HELM_WIN_HEXES:
            name = self.place_name(self.hex) or self.hex
            self.game_over = True
            self.won = True
            self.reason = (f'You return to {name} with the Royal Helm of the '
                           'Northlands and are instantly hailed as the '
                           'rightful King of the Northlands. Victory!')
        elif self.day > 70:
            self.game_over = True
            self.reason = 'Ten weeks have passed; the campaign is over.'
        elif not self.living():
            self.game_over = True
            self.reason = 'The party is gone.'
        else:
            if self.altar_blessed_day is not None \
                    and self.day - self.altar_blessed_day > self.ALTAR_BLESSING_DAYS:
                self.note('The High Altar blessing fades - you have run out '
                          'of time to reach the Northlands (e044).')
                self.altar_blessed_day = None
            if self.staff:
                self.note('You hold the Staff but are still south of the '
                          'Tragoth - you must carry it north to win (r212).')
            if self.helm and self.hex not in self.HELM_WIN_HEXES:
                self.note('You carry the Royal Helm - return to Ogon (0101) '
                          'or Weshor (1501) to be hailed King (e194).')
            self.note(f'Day {self.day} begins in hex {self.hex}.')
        return 'Day advanced.'

    # ------------------------------------------------------------ prison (e060-e063)
    def enter_prison(self, code):
        """e060-e063: the Prince is arrested.  e060 rolls for the gravity of
        the offence to pick the specific prison; gold, possessions and mounts
        are confiscated.  The stay is then resolved day by day in
        ``prison_step`` (escape or execution)."""
        if self.game_over:
            return
        if code == 'e060':
            die = self.d1()
            if die == 1:
                code = 'e061'
            elif die == 2:
                code = 'e062'
            elif die in (3, 4):
                code = 'e063'
            else:
                self._minor_offence()
                return
        self.imprisoned = code
        self.prison_days = 0
        self.moves_left = 0
        self.action = 'skip'
        self.gold = 0
        self.items = []
        self.staff = False
        self.helm = False
        for c in self.living():
            if c.mount != 'none':
                c.mount = 'none'
        if code == 'e062':
            # e062: the rest of the party is lost to the dungeon.
            self.party = [c for c in self.party if c.prince]
        self.note(f'You are arrested and imprisoned ({code}); gold, '
                  'possessions and mounts are confiscated.')

    def _minor_offence(self):
        """e060a: held overnight and fined 10 gold + 2 gold per character +
        1 gold per mount.  Pay to be released; if you cannot pay for yourself,
        you are imprisoned (e063)."""
        cost = 10 + 2 * len(self.living()) + sum(
            1 for c in self.living() if c.mount != 'none')
        if self.gold >= cost:
            self.gold -= cost
            self.note(f'Minor offence: you pay {cost} gold and are released '
                      '(e060a).')
            return
        self.gold = 0
        self.imprisoned = 'e063'
        self.prison_days = 0
        self.moves_left = 0
        self.action = 'skip'
        self.note('You cannot pay the fine - you are imprisoned (e063).')

    def prison_step(self):
        """Resolve one day in prison (e061/e062/e063): roll for escape or the
        headsman.  The day advances on each call; past day 70 the kingdom is
        lost.  e062 inflicts a poisoned wound every seven days."""
        self.day += 1
        self.prison_days += 1
        if self.day > 70:
            self.game_over = True
            self.won = False
            self.reason = 'You languish in prison until the ten weeks are up; ' \
                          'the kingdom is lost.'
            return
        if self.imprisoned == 'e061':
            die = self.d1()
            if die == 6:
                self.game_over = True
                self.won = False
                self.reason = 'You are led before the headsman and executed ' \
                              '(e061).'
                return
            if die == 1:
                self.note('Prison day: roll 1 - you escape (e061).')
                self.escape_prison('e061')
                return
            self.note(f'Prison day: roll {die} - you continue to languish '
                      '(e061).')
        elif self.imprisoned == 'e062':
            total = self.d2()
            if total in (2, 3):
                self.note(f'Prison day: roll {total} - you escape (e062).')
                self.escape_prison('e062')
                return
            if self.prison_days % 7 == 0:
                p = self.prince()
                if p:
                    p.wounds += 1
                    self.note(f'The dungeon takes its toll: the Prince gains '
                              f'a poisoned wound ({p.wounds}/{p.endurance}).')
                    if p.dead:
                        self.game_over = True
                        self.won = False
                        self.reason = 'The Prince dies in the dungeon (e062).'
                        return
            self.note(f'Prison day: roll {total} - you continue to languish '
                      '(e062).')
        elif self.imprisoned == 'e063':
            die = self.d1()
            if die == 1:
                self.note('Prison day: roll 1 - you escape (e063).')
                self.escape_prison('e063')
                return
            self.note(f'Prison day: roll {die} - you continue to languish '
                      '(e063).')

    def escape_prison(self, code):
        """The Prince escapes (r218): relocate to an adjacent hex and resolve
        which, if any, of the followers make it out.  e061: a follower escapes
        on a 1 or 2; e063: on a 1.  e062 already lost the rest of the party."""
        self.imprisoned = None
        escape_rolls = {1, 2} if code == 'e061' else {1}
        for c in self.party:
            if c.prince or not c.alive:
                continue
            if self.d1() in escape_rolls:
                self.note(f'{c.name} escapes with you.')
            else:
                c.alive = False
                self.note(f'{c.name} is left behind and lost.')
        self.party = [c for c in self.party if c.alive]
        self.escape_move()
        self.phase = 'action'
        self.action = 'skip'
        self.note('You are free again; the escape took the whole day (r218).')

    def daily_menu(self):
        kind = self.place_kind(self.hex)
        opts = []
        for label, act in self.ACTIONS:
            if act in ('news', 'audience') and kind not in ('town', 'castle', 'temple'):
                continue
            if act == 'offerings' and kind != 'temple':
                continue
            if act == 'ruins' and kind != 'ruins':
                continue
            if act == 'hire' and kind not in ('town', 'castle'):
                continue
            if act == 'cache' and self.hex not in self.caches:
                continue
            if act == 'raft' and not self.raft_available():
                continue
            # r215e: stores are sold for 1 gold a unit in a town, castle or
            # village, but only to a party that spends the whole day there.
            if act == 'buyfood' and kind not in ('town', 'castle', 'village',
                                                 'temple'):
                continue
            opts.append({'label': label,
                         'handler': (lambda a=act: self.begin_action(a))})
        opts.append({'label': 'End the day (food & lodging)',
                     'handler': (lambda: self.skip_day())})
        self.push('choice', f'Day {self.day} - action in hex {self.hex}',
                  f'You are in {self.model.travel_terrain(self.hex)} '
                  f'({self.model.terrain(self.hex)})'
                  + (f', at {self.place_name(self.hex)}' if self.place_name(self.hex) else '')
                  + '. Choose today\'s action (r203).', opts)

    # ------------------------------------------------------------ status
    def status(self):
        return {
            'day': self.day,
            'hex': self.hex,
            'terrain': self.model.terrain(self.hex),
            'travel_terrain': self.model.travel_terrain(self.hex),
            'place': self.place_name(self.hex),
            'gold': self.gold,
            'food': self.food,
            'wit': self.wit,
            'party': [c.name for c in self.living()],
            'party_detail': [(c.name, c.skill, c.endurance, c.wounds, c.mount,
                              c.guide, c.unreliable)
                             for c in self.living()],
            'caches': dict(self.caches),
            'items': list(self.items),
            'staff': self.staff,
            'helm': self.helm,
            'altar_blessed_day': self.altar_blessed_day,
            'imprisoned': self.imprisoned,
            'raft': self.raft,
            'raft_available': self.raft_available(),
            'game_over': self.game_over,
            'won': self.won,
            'reason': self.reason,
        }

    def run_until_idle(self, max_steps=200, chooser=None):
        """Resolve prompts automatically (used for testing / auto-play).

        ``chooser`` is any callable that takes the current prompt dict and
        returns an option index; without it the first option is always taken.
        """
        steps = 0
        while steps < max_steps:
            self.advance()
            if not self.prompts or self.game_over:
                break
            prompt = self.current()
            index = 0
            if chooser is not None:
                index = max(0, min(int(chooser(prompt)), len(prompt['options']) - 1))
            self.answer(index)
            steps += 1
        return steps

