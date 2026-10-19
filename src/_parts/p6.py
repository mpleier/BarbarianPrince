
    # ------------------------------------------------------------ prompt plumbing
    def push(self, kind, title, text, options):
        self.prompts.append({'kind': kind, 'title': title, 'text': text,
                             'options': options})

    def current(self):
        return self.prompts[0] if self.prompts else None

    def answer(self, index=0):
        p = self.prompts.pop(0)
        opt = p['options'][index]
        return opt['handler']()

    def is_busy(self):
        return bool(self.prompts)

    # ------------------------------------------------------------ encounters (r207)
    def encounter(self, code):
        ev = self.model.events.get(code)
        if not ev:
            self.note(f'(event {code} is not in the booklet - nothing happens)')
            return
        opts = parse_options(ev['text'])
        self.pending_event = {'code': code, 'title': ev['title'], 'text': ev['text'],
                              'headers': [], 'rows': []}
        if opts:
            headers, rows, note = opts
            self.pending_event.update({'headers': headers, 'rows': rows, 'note': note})
            self.push('encounter', f'{code} - {ev["title"]}',
                      ev['text'] + ('\n' + note if note else ''),
                      self.option_choices(headers))
        else:
            self.push('info', f'{code} - {ev["title"]}', ev['text'],
                      [{'label': 'Continue', 'handler': (lambda: 'Continuing.')}])

    def option_choices(self, headers):
        return [{'label': f'{h} (roll 2 dice)',
                 'handler': (lambda i=i: self.roll_option(i))}
                for i, h in enumerate(headers)]

    def roll_option(self, header_index):
        ev = self.pending_event
        dice = self.d2()
        row = None
        for roll, cells in ev['rows']:
            if roll == dice:
                row = cells
                break
        if not row:
            self.note(f'No entry for a roll of {dice}.')
            return 'Nothing happens.'
        cell = row[header_index] if header_index < len(row) else row[-1]
        label, ref = cell
        header = ev['headers'][header_index]
        self.note(f'{header} - rolled {dice}: {label} -> {ref}')
        return self.resolve_ref(ref, ev)

    def re_encounter(self):
        """Return to the event and pick another option (r314, r317, ...)."""
        ev = self.pending_event
        if not ev or not ev.get('headers'):
            return 'The encounter ends.'
        self.push('choice', f'{ev["code"]} - {ev["title"]} (try again)',
                  'That option failed. Choose another approach.',
                  self.option_choices(ev['headers']))
        return 'Choose another option.'
