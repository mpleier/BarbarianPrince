
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
    def resolve_ref(self, ref, ev=None):
        if not ref:
            return 'Nothing happens.'
        if ref in ('r300', 'r301', 'r302', 'r303', 'r304', 'r305', 'r306',
                   'r307', 'r308', 'r309', 'r310'):
            return self.start_combat(ev)
        if ref in ('r311', 'r312', 'r313', 'r314', 'r315'):
            return self.escape_ref(ref, ev)
        if ref in ('r316', 'r317', 'r318', 'r319', 'r320'):
            return self.hide_ref(ref, ev)
        if ref in ('r321', 'r322', 'r323', 'r324'):
            return self.bribe_ref(ref, ev)
        if ref in ('r325', 'r326', 'r327', 'r328', 'r329'):
            return self.pass_ref(ref, ev)
        if ref == 'r330':
            return self.forced_battle(ev)
        if ref in ('r331', 'r332', 'r333', 'r334', 'r335', 'r336', 'r337'):
            return self.hire_ref(ref, ev)
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
