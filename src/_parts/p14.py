
    # ------------------------------------------------------------ end of day
    def end_day(self):
        if self.combat:
            self.note('A battle is still in progress - the day cannot end.')
            return 'Day not finished.'
        self.feed_party()
        return 'End-of-day routines started.'

    def finish_day(self):
        """Called after food/lodging prompts are answered."""
        self.day += 1
        self.action = None
        self.pending_event = None
        if self.staff:
            self.game_over = True
            self.won = True
            self.reason = 'The Staff of Command has been recovered - the ' \
                         'Northlands are yours again.'
        elif self.day > 70:
            self.game_over = True
            self.reason = 'Ten weeks have passed; the campaign is over.'
        elif not self.living():
            self.game_over = True
            self.reason = 'The party is gone.'
        else:
            self.note(f'Day {self.day} begins in hex {self.hex}.')
        return 'Day advanced.'

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
            opts.append({'label': label,
                         'handler': (lambda a=act: self.begin_action(a))})
        opts.append({'label': 'End the day (food & lodging)',
                     'handler': (lambda: self.end_day())})
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
            'party_detail': [(c.name, c.skill, c.endurance, c.wounds, c.mount)
                             for c in self.living()],
            'caches': dict(self.caches),
            'items': list(self.items),
            'staff': self.staff,
            'game_over': self.game_over,
            'won': self.won,
            'reason': self.reason,
        }

    def run_until_idle(self, max_steps=200):
        """Resolve prompts automatically for testing / auto-play."""
        steps = 0
        while self.prompts and steps < max_steps:
            self.answer(0)
            steps += 1
        return steps
