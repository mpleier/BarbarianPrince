

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
    ]

    def __init__(self, model=None, features=None, seed=None, start_hex='0101'):
        self.model = model or GameModel.load()
        if features is None:
            with open(os.path.join(DATA, 'features.json'), encoding='utf-8') as f:
                features = json.load(f)
        self.features = features
        self.rng = random.Random(seed)
        self.log = []
        self.prompts = []
        self.day = 1
        self.hex = start_hex
        self.gold = 0
        self.food = 0
        self.caches = {}
        self.visited = {start_hex}
        self.items = []
        self.raft = False
        self.raft_days = 0
        self.news_bonus = {}
        self.offering_bonus = 0
        self.free_lodging = False
        self.staff = False
        self.party = []
        self.combat = None
        self.pending_event = None
        self.action = None
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
        raw = table[code][self.d1() - 1]
        raw = str(raw)
        item = None
        if '+' in raw:
            gold, letter = raw.split('+')
            item = f'Special possession {letter}'
        else:
            gold = raw
        return int(gold), item

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
        self.party.append(Character('Cal Arath (the Prince)', 8, 9, 2,
                                    prince=True))
        self.gold = 0
        self.note(f'The Barbarian Prince begins his quest in hex {self.hex}. '
                  f'Wit & wiles = {self.wit}.')

    def place(self, hid):
        return self.features['places'].get(hid)

    def place_name(self, hid):
        p = self.place(hid)
        return p['name'] if p else None

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
