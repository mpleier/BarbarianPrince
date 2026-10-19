
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
        for f in foes:
            f.pay = pay
            f.unreliable = unreliable
            f.town_leaver = town_leaver
            f.name = f.name.replace('Foe', 'Hired')
        self.party.extend(foes)
        self.note(f'{len(foes)} character(s) join the party at {pay} gold/day each.')
        return 'Followers acquired.'

    def refuse_roll(self, ev, mapping):
        die = self.d1()
        ref = mapping.get(die, 'r325')
        self.note(f'Refusal roll {die} -> {ref}')
        return self.resolve_ref(ref, ev)

    def hire_ref(self, ref, ev):
        amount = self.bribe_amount(ev)
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
