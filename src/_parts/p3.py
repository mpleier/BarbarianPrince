

class Combat:
    """r220 - round-by-round combat."""

    def __init__(self, party, foes, rng, party_first=True, name='Battle',
                 surprise=None, note=None):
        self.party = [c for c in party if not c.dead]
        self.foes = [c for c in foes if not c.dead]
        self.rng = rng
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
        return [(a, defenders[i % len(defenders)]) for i, a in enumerate(attackers)]

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
