
    # ------------------------------------------------------------ travel (r204, r205)
    def is_road_move(self, a, b):
        return frozenset((a, b)) in self.features['road_sides']

    def is_river_move(self, a, b):
        return frozenset((a, b)) in self.features['river_sides']

    def check_lost(self, terrain):
        """r205 - roll 2 dice vs the terrain threshold; a guide subtracts 1."""
        row = self.model.travel_row(terrain)
        thr = threshold(row['lost']) if row else None
        if thr is None:
            return False
        r = self.d2() - (1 if self.has_guide() else 0)
        self.note(f'Getting lost check [{terrain}]: rolled {r} vs {thr}+ '
                  + ('-> LOST' if r >= thr else '-> ok'))
        return r >= thr

    def travel_event(self, hid, road=False, flying=False, rafting=False):
        terrain = ('Rafting' if rafting else 'On Road' if road
                   else 'Airborne' if flying
                   else self.model.travel_terrain(hid))
        row = self.model.travel_row(terrain)
        if not row:
            return
        thr = threshold(row['event_threshold'])
        r = self.d2()
        if thr is not None and r >= thr:
            die = self.d1()
            ref = row['event_refs'][die - 1]
            code = self.model.resolve_event_ref(ref, die)
            self.note(f'Travel event [{terrain}]: rolled {r} (needs {thr}+), '
                      f'die {die} -> {ref} -> {code}')
            self.encounter(code)
        else:
            self.note(f'No travel event [{terrain}]: rolled {r} (needs {thr}+).')

    def begin_travel(self):
        self.action = 'travel'
        self.moves_left = self.speed()
        self.flying = self.speed() == 3
        self.note(f'Travel action: the party moves {self.moves_left} hex/day '
                  + ('(airborne)' if self.flying else
                     '(mounted)' if self.speed() == 2 else '(on foot)'))
        self.choose_move()

    def choose_move(self):
        nbs = self.model.neighbors(self.hex)
        opts = []
        for d, hid in sorted(nbs.items()):
            label = f'{d} -> {hid} ({self.model.travel_terrain(hid)})'
            if self.is_road_move(self.hex, hid):
                label += ' [road]'
            if self.is_river_move(self.hex, hid):
                label += ' [river]'
            opts.append({'label': label,
                         'handler': (lambda hid=hid: self.move(hid))})
        opts.append({'label': 'Stop travelling for the day',
                     'handler': (lambda: self.stop_travel())})
        self.push('choice', f'Move ({self.moves_left} hex(es) left)',
                  f'In hex {self.hex}. Choose the next hex to enter (r204).', opts)

    def stop_travel(self):
        self.moves_left = 0
        self.note('The party stops travelling for the day.')
        return 'Travel ended.'

    def move(self, dest):
        src = self.hex
        if self.moves_left <= 0:
            self.note('No movement left this day.')
            return False
        if dest not in self.model.neighbors(src):
            self.note(f'{dest} is not adjacent to {src}.')
            return False
        road = self.is_road_move(src, dest)
        river = self.is_river_move(src, dest)
        self.note(f'Travel {src} -> {dest}: {self.model.travel_terrain(src)} -> '
                  f'{self.model.travel_terrain(dest)}'
                  + (' [road]' if road else '') + (' [river]' if river else ''))
        if not road and self.check_lost('Airborne' if self.flying
                                        else self.model.travel_terrain(src)):
            self.note('Lost while leaving: the day is spent wandering, checking the '
                      'hex you tried to enter (r205b).')
            self.moves_left = 0
            self.travel_event(dest, road=road, flying=self.flying)
            return False
        if river and not road and not self.flying:
            if self.check_lost('Cross River'):
                self.note('No crossing found - the party stays in ' + src + '.')
                self.moves_left = 0
                return False
            self.note('The river is crossed.')
        if not road and self.check_lost(self.model.travel_terrain(dest)):
            self.note(f'Lost entering {dest}: the day ends back in {src}.')
            self.moves_left = 0
            self.travel_event(dest, road=road, flying=self.flying)
            return False
        self.hex = dest
        self.moves_left -= 1
        self.visited.add(dest)
        self.travel_event(dest, road=road, flying=self.flying)
        return True
