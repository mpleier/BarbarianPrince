
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
            if c.wounds > 0:
                c.wounds -= 1
                self.note(f'{c.name} heals a wound ({c.wounds}/{c.endurance}).')
        if combat_or_escape:
            self.note('The rest was disturbed, so no wounds are healed.')
        return 'Rested and healed.'

    # ------------------------------------------------------------ food (r215, r216)
    def foraging_ok(self):
        t = self.model.terrain(self.hex)
        return t in ('farmland', 'countryside', 'forest', 'hills')

    def food_need(self):
        need = len(self.living())
        if not self.foraging_ok():
            need += 2 * sum(1 for c in self.living() if c.mount != 'none')
        if self.model.terrain(self.hex) == 'desert':
            need *= 2
        return need

    def feed_party(self):
        need = self.food_need()
        kind = self.place_kind(self.hex)
        opts = []
        if self.food >= need:
            opts.append({'label': f'Eat from stores ({need} units)',
                         'handler': (lambda: self.eat_stores(need))})
        if kind in ('town', 'castle', 'temple'):
            opts.append({'label': f'Buy meals ({need} gold)',
                         'handler': (lambda: self.buy_meals(need))})
        if not (kind in ('town', 'castle', 'temple')):
            opts.append({'label': 'Go hunting (r215b)',
                         'handler': (lambda: self.hunt(need))})
        opts.append({'label': 'Go hungry (r216)',
                     'handler': (lambda: self.starve(need))})
        self.push('choice', f'Evening meal - need {need} food units',
                  f'Party needs {need} food units; you have {self.food} in stores.',
                  opts)

    def eat_stores(self, need):
        self.food -= need
        self.note(f'Ate {need} food units from stores.')
        return 'Fed.'

    def buy_meals(self, need):
        if self.gold >= need:
            self.gold -= need
            self.note(f'Bought meals for {need} gold.')
            return 'Fed.'
        self.note('Not enough gold to buy meals.')
        return self.starve(need)

    def hunt(self, need):
        hunter = max(self.living(), key=lambda c: c.skill + c.remaining // 2)
        total = hunter.skill + hunter.remaining // 2
        total += sum(1 for c in self.living() if c.guide)
        dice = self.d2()
        gained = total - dice
        self.note(f'Hunting by {hunter.name}: {total} - {dice} = {gained} units.')
        if dice == 12:
            wounds = self.d1()
            hunter.wounds += wounds
            self.note(f'The hunter is hurt: {wounds} wounds '
                      f'({hunter.wounds}/{hunter.endurance})'
                      + (' -> dead' if hunter.dead else ''))
            if hunter.dead:
                hunter.alive = False
                gained = 0
        if self.model.terrain(self.hex) == 'farmland':
            die = self.d1()
            if die == 5:
                self.note('Peasant mob in pursuit (e017).')
                self.encounter('e017')
            elif die == 6:
                self.note('Pursued by constabulary (e050).')
                self.encounter('e050')
        if gained > 0:
            self.food += gained
            self.note(f'Hunt yields {gained} food units.')
        if gained < need:
            self.note(f'Still short {need - gained} units - some go hungry.')
            self.starve(need - gained)
        return 'Hunted.'

    def starve(self, shortfall):
        self.note(f'{shortfall} food unit(s) short - starvation (r216).')
        for c in self.living():
            if c.prince:
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
