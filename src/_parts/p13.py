
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
        self.note(f'Bought horses; party now mounted.')
        return 'Horses bought.'

    # ------------------------------------------------------------ lodging (r217)
    def lodging(self):
        kind = self.place_kind(self.hex)
        if kind not in ('town', 'castle', 'temple'):
            return 'Camp for the night in the open.'
        special = sum(1 for c in self.living()
                      if any(w in c.name.lower() for w in
                             ('priest', 'monk', 'magician', 'wizard', 'witch')))
        others = len(self.living()) - special
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
