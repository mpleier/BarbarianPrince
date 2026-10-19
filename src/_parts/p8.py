
    # ------------------------------------------------------------ escape & hide (r218)
    def escape_move(self):
        """Move randomly to an adjacent hex; rivers and off-map are re-rolled."""
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
    def bribe_amount(self, ev):
        if not ev:
            return 10
        m = re.search(r'(\d+)\s*(?:gold|gp)', ev['text'])
        return int(m.group(1)) if m else 10

    def bribe_ref(self, ref, ev):
        amount = self.bribe_amount(ev)
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
