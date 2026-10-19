
    # ------------------------------------------------------------ daily actions
    def begin_action(self, action):
        self.action = action
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
            return self.raft_action()
        if action == 'explore':
            return self.explore()
        return 'Unknown action.'

    def seek_news(self):
        """r209 - seek news & information: 2 dice, +1 per follower with skill 6+."""
        bonus = sum(1 for c in self.living() if c.skill >= 6)
        total = self.d2() + bonus
        self.note(f'Seeking news: rolled {total} (bonus {bonus}).')
        if total <= 10:
            self.note('Nothing learned - the day is wasted.')
            return 'Nothing learned.'
        kind = self.place_kind(self.hex)
        if kind in ('Town', 'Castle', 'Temple'):
            self.note(f'You learn about the {kind} in hex {self.hex}.')
            self.push('info', f'News about {kind} in {self.hex}',
                      'You gather useful information about this place.',
                      [{'label': 'Continue', 'handler': (lambda: 'Continuing.')}])
            return 'News gathered.'
        self.note('You learn nothing specific about this hex.')
        return 'Nothing learned.'

    def search_ruins(self):
        """r208 - search the ruins: 2 dice, +1 per follower with skill 6+."""
        bonus = sum(1 for c in self.living() if c.skill >= 6)
        total = self.d2() + bonus
        self.note(f'Searching the ruins: rolled {total} (bonus {bonus}).')
        if total <= 10:
            self.note('Nothing found - the day is wasted.')
            return 'Nothing found.'
        code = RUINS.get(total, 'r325')
        self.note(f'Ruins roll {total} -> {code}')
        self.encounter(code)
        return 'Ruins searched.'

    def recover_cache(self):
        """r214 - recover a hidden cache buried in this hex."""
        if self.hex not in self.caches:
            self.note('There is no cache hidden in this hex.')
            return 'No cache here.'
        code, amount = self.caches.pop(self.hex)
        gold, item = self.treasure_roll(code)
        self.gold += gold
        if item:
            self.items.append(item)
        self.note(f'Recovered the cache: {gold} gold' + (f' + {item}' if item else ''))
        return 'Cache recovered.'

    def raft_action(self):
        """r213 - raft down the river: 2 dice, +1 per follower with skill 6+."""
        bonus = sum(1 for c in self.living() if c.skill >= 6)
        total = self.d2() + bonus
        self.note(f'Rafting: rolled {total} (bonus {bonus}).')
        if total <= 10:
            self.note('The raft is lost and the day is wasted.')
            self.raft = False
            return 'Raft lost.'
        code = RAFTING.get(total, 'r325')
        self.note(f'Rafting roll {total} -> {code}')
        self.raft_days += 1
        self.encounter(code)
        return 'Rafting continues.'

    def seek_audience(self):
        """r211 - seek an audience: 2 dice, +1 per follower with skill 6+."""
        kind = self.place_kind(self.hex)
        if kind not in ('Town', 'Castle', 'Temple'):
            self.note('There is nobody here to grant an audience.')
            return 'No audience available.'
        bonus = sum(1 for c in self.living() if c.skill >= 6)
        total = self.d2() + bonus
        self.note(f'Seeking an audience in {kind} {self.hex}: rolled {total}.')
        if total <= 10:
            self.note('The audience is refused - the day is wasted.')
            return 'Audience refused.'
        code = AUDIENCE.get(total, 'r325')
        self.note(f'Audience roll {total} -> {code}')
        self.encounter(code)
        return 'Audience sought.'

    def make_offerings(self):
        """r212 - submit offerings at a temple or town."""
        kind = self.place_kind(self.hex)
        if kind not in ('Town', 'Temple', 'Castle'):
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
                  f'How much gold do you offer in {kind} {self.hex}?', opts)
        return 'Choose an offering.'

    def offering(self, amount):
        self.gold -= amount
        code = OFFERINGS.get(min(100, amount), 'r325')
        self.note(f'Offering of {amount} gold -> {code}')
        self.encounter(code)
        return 'Offerings made.'
