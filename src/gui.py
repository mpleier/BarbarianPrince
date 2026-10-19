"""Tkinter interface for the Barbarian Prince engine.

Layout:
  * left  - the hex map (terrain, roads, rivers, named places, party marker)
  * right - party status, the adventure log and the current prompt with buttons

The GUI is deliberately thin: it only renders the prompt queue produced by
``engine.Game`` and feeds the player's choice back into ``Game.resolve``.
"""
import math
import tkinter as tk
from tkinter import ttk

from features import load_features
from geometry import R, DX, DY

TERRAIN_COLORS = {
    'farmland': '#dfe9b0',
    'countryside': '#a9d18a',
    'forest': '#2f7d43',
    'mountains': '#c9c9d8',
    'hills': '#c3a976',
    'badlands': '#b0655f',
    'swamp': '#7fb6a8',
    'desert': '#f2d98c',
    'dead': '#b3b3b3',
    'ice': '#e6f0f5',
    'water': '#7fb2d8',
    'unknown': '#d8d8d8',
}

PLACE_SYMBOL = {
    'town': 'o', 'village': 'o', 'fort': '*', 'castle': '*', 'tower': '*',
    'temple': '+', 'shrine': '+', 'ruin': 'x', 'mine': '#', 'farm': 'f',
    'hollow': 'h', 'pool': '~', 'inn': 'i', 'cave': 'c', 'camp': 'c',
    'city': 'O',
}


class MapCanvas:
    """Draws the 20x23 board on a tkinter canvas."""

    def __init__(self, canvas, grid, features, scale=0.24):
        self.canvas = canvas
        self.grid = grid
        self.features = features
        self.scale = scale
        xs = [h['center'][0] for h in grid.values()]
        ys = [h['center'][1] for h in grid.values()]
        self.minx, self.maxx = min(xs) - R, max(xs) + R
        self.miny, self.maxy = min(ys) - R, max(ys) + R
        self.w = (self.maxx - self.minx) * scale
        self.h = (self.maxy - self.miny) * scale
        canvas.configure(width=self.w, height=self.h)

    def px(self, x, y):
        return ((x - self.minx) * self.scale, (y - self.miny) * self.scale)

    def hex_points(self, h):
        # The board is a flat-top hex grid (columns spaced 1.5R, rows sqrt(3)R),
        # so the vertices sit at 0, 60, 120, ... degrees.
        cx, cy = self.px(h['center'][0], h['center'][1])
        return [(cx + self.scale * R * math.cos(math.radians(a)),
                 cy + self.scale * R * math.sin(math.radians(a)))
                for a in (0, 60, 120, 180, 240, 300)]

    def draw(self, game):
        self.canvas.delete('all')
        for hid, h in self.grid.items():
            pts = self.hex_points(h)
            color = TERRAIN_COLORS.get(h['terrain'], 'unknown')
            self.canvas.create_polygon(pts, fill=color, outline='#555',
                                       width=1, tags='hex')
            cx, cy = self.px(h['center'][0], h['center'][1])
            self.canvas.create_text(cx, cy, text=hid, font=('Arial', 7),
                                    fill='#333', tags='label')

        # rivers: the shared edge between two hexes
        for a, b in self.features['river_sides']:
            if a not in self.grid or b not in self.grid:
                continue
            ha, hb = self.grid[a], self.grid[b]
            vx, vy = hb['center'][0] - ha['center'][0], hb['center'][1] - ha['center'][1]
            n = math.hypot(vx, vy)
            nx, ny = -vy / n * R / 2, vx / n * R / 2
            mx, my = (ha['center'][0] + hb['center'][0]) / 2, (ha['center'][1] + hb['center'][1]) / 2
            p1 = self.px(mx + nx, my + ny)
            p2 = self.px(mx - nx, my - ny)
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill='#2b6fb5', width=3, tags='river')

        # roads: line between the two hex centres
        for a, b in self.features['road_sides']:
            if a not in self.grid or b not in self.grid:
                continue
            p1 = self.px(self.grid[a]['center'][0], self.grid[a]['center'][1])
            p2 = self.px(self.grid[b]['center'][0], self.grid[b]['center'][1])
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill='#8a5a2b', width=3, tags='road')

        for hid, place in self.features['places'].items():
            if hid not in self.grid:
                continue
            cx, cy = self.px(self.grid[hid]['center'][0], self.grid[hid]['center'][1])
            sym = PLACE_SYMBOL.get(place['kind'], 'o')
            self.canvas.create_text(cx, cy - 9, text=sym, font=('Arial', 9, 'bold'),
                                    fill='#7a2f2f', tags='place')
            self.canvas.create_text(cx, cy + 13, text=place['name'], font=('Arial', 7),
                                    fill='#7a2f2f', tags='place')

        for hid in game.visited:
            if hid in self.grid:
                cx, cy = self.px(self.grid[hid]['center'][0], self.grid[hid]['center'][1])
                self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                                        fill='#333', outline='')

        cx, cy = self.px(self.grid[game.hex]['center'][0], self.grid[game.hex]['center'][1])
        self.canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill='#e03131',
                                outline='#7a1010', width=2, tags='party')
        self.canvas.create_text(cx, cy, text='P', fill='white',
                                font=('Arial', 8, 'bold'), tags='party')


class GameGUI:
    def __init__(self, game):
        self.game = game
        self.features = load_features()
        self.root = tk.Tk()
        self.root.title('Barbarian Prince')
        self.root.geometry('1280x820')

        main = ttk.Frame(self.root)
        main.pack(fill='both', expand=True)

        left = ttk.Frame(main)
        left.pack(side='left', fill='both', expand=True)
        self.map = MapCanvas(tk.Canvas(left, bg='#f4f1e8'),
                            game.model.grid, self.features)
        self.map.canvas.pack(fill='both', expand=True)

        right = ttk.Frame(main, width=360)
        right.pack(side='right', fill='both')

        self.status = tk.Text(right, height=10, font=('Arial', 10))
        self.status.pack(fill='x')

        self.log = tk.Text(right, height=22, font=('Arial', 9))
        self.log.pack(fill='both', expand=True)

        self.prompt_title = tk.Label(right, font=('Arial', 12, 'bold'))
        self.prompt_title.pack()
        self.prompt_body = tk.Label(right, font=('Arial', 9), wraplength=340)
        self.prompt_body.pack()
        self.buttons = ttk.Frame(right)
        self.buttons.pack(fill='x')

        self.map.draw(game)
        self.refresh_status()
        self.log_index = 0

    def refresh_status(self):
        g = self.game
        lines = [f'Day {g.day}  |  Hex {g.hex} ({g.model.travel_terrain(g.hex)})'
                 + ('  [airborne]' if g.flying else '')]
        lines.append(f'Gold: {g.gold}   Food: {g.food}   Wit & wiles: {g.wit}')
        lines.append(f'Movement left: {g.moves_left}   Speed: {g.speed()} hex/day')
        lines.append('')
        for c in g.living():
            lines.append(f'  {c.name}: skill {c.skill}, endurance {c.endurance}, '
                         f'wounds {c.wounds}, mount {c.mount}'
                         + (' [guide]' if c.guide else '')
                         + (' [unreliable]' if c.unreliable else ''))
        if g.combat:
            lines.append('')
            lines.append('COMBAT: ' + g.combat.name + ' (round '
                         + str(g.combat.round) + ')')
            for side, units in (('party', g.combat.party), ('foes', g.combat.foes)):
                for e in units:
                    if not e.dead:
                        lines.append(f'  {side}: {e.name} {e.endurance - e.wounds}/'
                                     f'{e.endurance}')
        if g.caches:
            lines.append('')
            lines.append('Caches: ' + ', '.join(
                f'{k} ({v})' for k, v in g.caches.items()))
        self.status.delete('1.0', 'end')
        self.status.insert('1.0', '\n'.join(lines))
        self.map.draw(g)

    def drain_notes(self):
        for line in self.game.log[self.log_index:]:
            self.log_line(line)
        self.log_index = len(self.game.log)

    def log_line(self, text):
        self.log.insert('end', text + '\n')
        self.log.see('end')

    def ask(self, prompt):
        self.prompt_title.configure(text=prompt['title'])
        self.prompt_body.configure(text=prompt['text'])
        for w in self.buttons.winfo_children():
            w.destroy()
        chosen = tk.Variable()
        for i, opt in enumerate(prompt['options']):
            tk.Button(self.buttons, text=opt['label'],
                      command=lambda i=i: chosen.set(i)).pack(fill='x')
        self.root.wait_variable(chosen)
        return chosen.get()

    def run(self):
        g = self.game
        while not g.game_over:
            self.drain_notes()
            self.refresh_status()
            g.advance()
            while g.prompts and not g.game_over:
                self.drain_notes()
                self.refresh_status()
                p = g.current()
                if p['kind'] == 'info' or not p['options']:
                    self.log_line('>> ' + p['title'] + ': ' + p['text'])
                    g.answer(0)
                    continue
                choice = self.ask(p)
                g.answer(choice)
            self.drain_notes()
            self.refresh_status()
        self.drain_notes()
        self.log_line('*** ' + (g.reason or 'Game over'))
        self.prompt_title.configure(text='Game over: ' + (g.reason or ''))
        self.prompt_body.configure(text='')
        for w in self.buttons.winfo_children():
            w.destroy()
        tk.Button(self.buttons, text='Close', command=self.root.destroy).pack()
        self.root.mainloop()


def main(seed=None):
    from engine import Game
    GameGUI(Game(seed=seed)).run()


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--cli', action='store_true', help='play in the terminal')
    args = ap.parse_args()
    if args.cli:
        from cli import play_cli
        play_cli(args.seed)
    else:
        main(args.seed)
