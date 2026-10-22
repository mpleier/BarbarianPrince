"""Query API over the unified BarbarianPrince game model.

The model is produced by src/build_model.py and stored in data/game_model.json.
It merges:
  * the 20x23 hex grid (geometry + terrain classification)
  * rule sections r201-r343
  * every structured table (travel, combat, treasure, news, hiring, offerings,
    audience, cache recovery, traps, errata, ...)
  * event sections e001-e195 and their encounter option matrices

Dice helpers follow the booklet convention: "10+" means "10 or more", and a
row spec such as "6,7,8" matches any of those totals.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, 'data', 'game_model.json')


class GameModel:
    def __init__(self, model):
        self.grid = model['grid']
        self.rules = model['rules']
        self.tables = model['tables']
        self.events = model['events']
        self.options = model['event_options']
        self.index = model['index']
        self.geometry = model['geometry']
        self.meta = model['meta']

    @classmethod
    def load(cls, path=MODEL_PATH):
        with open(path, encoding='utf-8') as f:
            return cls(json.load(f))

    # ---------------------------------------------------------------- grid
    def hex(self, hid):
        return self.grid[hid]

    def terrain(self, hid):
        return self.grid[hid]['terrain']

    def travel_terrain(self, hid):
        return self.grid[hid]['travel_terrain']

    def neighbors(self, hid):
        return self.grid[hid]['neighbors']

    def path_neighbors(self, hid):
        return list(self.grid[hid]['neighbors'].values())

    def hexes_by_terrain(self, terrain):
        return [h for h in self.grid.values() if h['terrain'] == terrain]

    def distance(self, a, b):
        """Hex distance in the axial-ish offset coordinate system (approximate,
        computed by BFS over the neighbour graph)."""
        from collections import deque
        seen = {a: 0}
        q = deque([a])
        while q:
            cur = q.popleft()
            if cur == b:
                return seen[cur]
            for n in self.grid[cur]['neighbors'].values():
                if n not in seen:
                    seen[n] = seen[cur] + 1
                    q.append(n)
        return None


    # ---------------------------------------------------------------- dice
    @staticmethod
    def matches(row, total):
        rolls = row.get('rolls') or []
        if total in rolls:
            return True
        if row.get('open_ended') and rolls and total > max(rolls):
            return True
        return False

    def roll_row(self, rows, total):
        for row in rows:
            if self.matches(row, total):
                return row
        return None

    # ---------------------------------------------------------------- tables
    def travel_row(self, terrain):
        for row in self.tables['travel_table']:
            if row['terrain'] == terrain:
                return row
        return None

    def travel_event_ref(self, terrain, die_roll):
        """Travel Table: roll one die, read across to the event reference."""
        row = self.travel_row(terrain)
        if not row:
            return None
        refs = row['event_refs']
        return refs[die_roll - 1] if 1 <= die_roll <= len(refs) else None

    def resolve_event_ref(self, ref, die_roll):
        """r231-r280 reference -> concrete event code for a one-die roll."""
        refs = self.tables['travel_event_refs'].get(ref)
        if not refs:
            return ref
        return refs[die_roll - 1] if 1 <= die_roll <= len(refs) else ref

    def combat_wounds(self, strike_total):
        return self.tables['combat_table'].get(str(strike_total))

    def audience(self, host, total):
        return self.roll_row(self.tables['audience'][host]['rows'], total)

    def news(self, total):
        return self.roll_row(self.tables['news'], total)

    def hiring(self, total):
        return self.roll_row(self.tables['hiring'], total)

    def offerings(self, total):
        return self.roll_row(self.tables['offerings'], total)

    def raft_event(self, total):
        return self.tables['raft_travel_events'].get(str(total))

    def event(self, code):
        return self.events[code]

    def event_options(self, code):
        return self.options.get(code)

    def rule(self, rid):
        return self.rules[rid]

    def errata_for(self, section):
        return [e for e in self.tables['errata'] if e['section'] == section]


if __name__ == '__main__':
    m = GameModel.load()
    print('hexes', len(m.grid), '| rules', len(m.rules), '| events', len(m.events))
    print('0101 terrain:', m.terrain('0101'), '-> travel terrain', m.travel_terrain('0101'))
    print('neighbors of 1212:', m.neighbors('1212'))
    print('Baron audience roll 12:', m.audience('the Baron of Huldra Castle', 12))
    ref = m.travel_event_ref('Forest', 3)
    print('travel ref for Forest, roll 3:', ref, '-> event', m.resolve_event_ref(ref, 4))
