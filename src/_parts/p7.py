
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
        total = self.d2() + modifier
        ref = BATTLE_REFERENCE.get(min(12, max(2, total)), 'r306')
        self.note(f'Battle reference: rolled {total} -> {ref}')
        first, surprise = self.battle_situation(ref)
        foes = parse_foes(ev['text'] if ev else '')
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
        result = self.combat.step()
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
            for foe in c.foes:
                if foe.alive:
                    gold, item = self.treasure_roll(foe.wealth)
                    self.gold += gold
                    if item:
                        self.items.append(item)
                    self.note(f'Loot from {foe.name}: {gold} gold'
                              + (f' + {item}' if item else ''))
        self.combat = None
        self.party = [x for x in self.party if x.alive]
        if not self.living():
            self.game_over = True
            self.reason = 'The whole party has been wiped out.'
        return f'Combat over ({c.result}).'
