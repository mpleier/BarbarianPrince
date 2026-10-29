"""Tkinter interface for the Barbarian Prince engine.

Layout:
  * left  - the hex map (terrain, roads, rivers, named places, party marker)
  * right - party status, the adventure log and the current prompt with buttons

The GUI is deliberately thin: it only renders the prompt queue produced by
``engine.Game`` and feeds the player's choice back into ``Game.resolve``.
"""
import math
import os
import tempfile
import tkinter as tk
from tkinter import ttk

from autoplay import Bot, STRATEGIES
from engine import Game
from features import load_features
from geometry import R
from map_scan import stitch, scan_rect

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

# Board scales: the canvas is bigger than the window at the larger settings
# and scrolls inside its frame.
ZOOM = {'small': 0.16, 'medium': 0.24, 'large': 0.34, 'huge': 0.45}

PLACE_SYMBOL = {
    'town': 'o', 'village': 'o', 'fort': '*', 'castle': '*', 'tower': '*',
    'temple': '+', 'shrine': '+', 'ruin': 'x', 'mine': '#', 'farm': 'f',
    'hollow': 'h', 'pool': '~', 'inn': 'i', 'cave': 'c', 'camp': 'c',
    'city': 'O',
}


class MapCanvas:
    """Draws the 20x23 board on a tkinter canvas.

    ``mode`` selects how the map is drawn:
      * 'vector' - flat terrain fills (the default)
      * 'scan'   - the original board artwork, hexes as thin outlines only

    (The web front-end also has a 'blend' mode; tkinter cannot do
    translucent fills, so the desktop map offers only the two above.)
    """

    def __init__(self, canvas, grid, features, scale=0.24, mode='vector'):
        self.canvas = canvas
        self.grid = grid
        self.features = features
        self.scale = scale
        self.mode = mode
        self.show_grid = True
        self.show_ids = True
        self.show_traces = True
        self.show_names = True
        self.show_symbols = True
        self._scan_photo = None
        xs = [h['center'][0] for h in grid.values()]
        ys = [h['center'][1] for h in grid.values()]
        self.minx, self.maxx = min(xs) - R, max(xs) + R
        self.miny, self.maxy = min(ys) - R, max(ys) + R
        self.w = (self.maxx - self.minx) * scale
        self.h = (self.maxy - self.miny) * scale
        canvas.configure(width=self.w, height=self.h)

    def scan_photo(self):
        """The stitched board scan scaled to the canvas, as a tk.PhotoImage.

        Built in memory: tk.PhotoImage cannot read a PNG from PIL directly, so
        PIL's ImageTk does the conversion and nothing is written to disk.
        """
        if self._scan_photo is not None:
            return self._scan_photo
        rect = scan_rect()
        if not rect:
            return None
        sx, sy, sw, sh = rect
        img = stitch(width=max(1, int(sw * self.scale)))
        if img is None:
            return None
        try:
            from PIL import ImageTk
            self._scan_photo = ImageTk.PhotoImage(img)
        except Exception:
            # ImageTk unavailable: fall back to a temp file and remove it.
            path = os.path.join(tempfile.gettempdir(), 'bp_board_scan.png')
            img.save(path)
            try:
                self._scan_photo = tk.PhotoImage(file=path)
            finally:
                try:
                    os.remove(path)
                except OSError:
                    pass
        self._scan_offset = self.px(sx, sy)
        return self._scan_photo

    def set_scale(self, scale):
        """Resize the board; the cached scan image is rebuilt at the new size."""
        self.scale = scale
        self.w = (self.maxx - self.minx) * scale
        self.h = (self.maxy - self.miny) * scale
        self._scan_photo = None
        self.canvas.configure(width=self.w, height=self.h)

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
        self.canvas.configure(scrollregion=(0, 0, self.w, self.h))
        mode = self.mode
        if mode == 'scan':
            photo = self.scan_photo()
            if photo:
                ox, oy = self._scan_offset
                self.canvas.create_image(ox, oy, image=photo, anchor='nw',
                                         tags='scan')
            else:
                # No board scan available (a checkout without _refs): fall back
                # to the terrain fills rather than drawing an empty map.
                mode = 'vector'
        for hid, h in self.grid.items():
            pts = self.hex_points(h)
            color = '' if mode == 'scan' else TERRAIN_COLORS.get(h['terrain'], 'unknown')
            outline = '' if not self.show_grid else ('#ffffff' if mode == 'scan' else '#555')
            self.canvas.create_polygon(pts, fill=color, outline=outline,
                                       width=1, tags='hex')
            if self.show_ids:
                cx, cy = self.px(h['center'][0], h['center'][1])
                self.canvas.create_text(cx, cy, text=hid, font=('Arial', 7),
                                        fill='#333', tags='label')

        if self.show_traces:
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
            if not (self.show_names or self.show_symbols):
                continue
            cx, cy = self.px(self.grid[hid]['center'][0], self.grid[hid]['center'][1])
            sym = PLACE_SYMBOL.get(place['kind'], 'o')
            if self.show_symbols:
                self.canvas.create_text(cx, cy - 9, text=sym,
                                        font=('Arial', 9, 'bold'),
                                        fill='#7a2f2f', tags='place')
            if self.show_names:
                self.canvas.create_text(cx, cy + 13, text=place['name'],
                                        font=('Arial', 7), fill='#7a2f2f',
                                        tags='place')

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

        # The bot plays through the same prompt queue the player does, so
        # "Bot move" answers one prompt and "Auto-play" keeps going.
        self.bot = Bot(game, 'balanced', variety=0.3)
        self.auto = False
        self.delay = 250            # ms between bot answers (4 steps/s)
        self._after = None          # pending tick, so restart cannot double it

        main = ttk.Frame(self.root)
        main.pack(fill='both', expand=True)

        left = ttk.Frame(main)
        left.pack(side='left', fill='both', expand=True)

        bar = ttk.Frame(left)
        bar.pack(fill='x', padx=6, pady=4)
        ttk.Label(bar, text='Map:').pack(side='left')
        # Default to the board artwork with the overlays off: the scanned map
        # already draws the rivers, roads and hex ids of the original board.
        self.map_mode = tk.StringVar(value='scan')
        box = ttk.Combobox(bar, textvariable=self.map_mode,
                           values=['vector', 'scan'], state='readonly', width=10)
        box.pack(side='left')
        box.bind('<<ComboboxSelected>>', self.on_map_mode)
        self.show_grid = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text='hex grid', variable=self.show_grid,
                        command=self.redraw).pack(side='left')
        self.show_ids = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text='hex ids', variable=self.show_ids,
                       command=self.redraw).pack(side='left')
        self.show_traces = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text='rivers & roads', variable=self.show_traces,
                       command=self.redraw).pack(side='left')
        self.show_names = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text='place names', variable=self.show_names,
                       command=self.redraw).pack(side='left')
        ttk.Label(bar, text='  size:').pack(side='left')
        self.zoom = tk.StringVar(value='medium')
        zoom = ttk.Combobox(bar, textvariable=self.zoom,
                            values=['small', 'medium', 'large', 'huge'],
                            state='readonly', width=8)
        zoom.pack(side='left')
        zoom.bind('<<ComboboxSelected>>', self.on_zoom)

        # The board is bigger than the window at the larger sizes, so it lives
        # in a canvas with scrollbars rather than being squashed to fit.
        wrap = ttk.Frame(left)
        wrap.pack(fill='both', expand=True)
        self.hbar = ttk.Scrollbar(wrap, orient='horizontal')
        self.vbar = ttk.Scrollbar(wrap, orient='vertical')
        self.map = MapCanvas(
            tk.Canvas(wrap, bg='#f4f1e8',
                      xscrollcommand=self.hbar.set,
                      yscrollcommand=self.vbar.set),
            game.model.grid, self.features,
            mode=self.map_mode.get(), scale=ZOOM[self.zoom.get()])
        self.hbar.configure(command=self.map.canvas.xview)
        self.vbar.configure(command=self.map.canvas.yview)
        self.vbar.pack(side='right', fill='y')
        self.hbar.pack(side='bottom', fill='x')
        self.map.canvas.pack(side='left', fill='both', expand=True)
        self.map.show_grid = bool(self.show_grid.get())
        self.map.show_ids = bool(self.show_ids.get())
        self.map.show_traces = bool(self.show_traces.get())
        self.map.show_names = bool(self.show_names.get())

        right = ttk.Frame(main, width=360)
        right.pack(side='right', fill='both')

        self.status = tk.Text(right, height=10, font=('Arial', 10))
        self.status.pack(fill='x')

        self.log = tk.Text(right, height=22, font=('Arial', 9), wrap='word')
        self.log.pack(fill='both', expand=True)

        # --- autoplay controls -------------------------------------------
        controls = ttk.Frame(right)
        controls.pack(fill='x', pady=(4, 0))
        self.btn_restart = ttk.Button(controls, text='New game',
                                      command=self.restart, width=10)
        self.btn_restart.pack(side='left')
        self.btn_bot = ttk.Button(controls, text='Bot move',
                                  command=self.bot_move, width=10)
        self.btn_bot.pack(side='left', padx=4)
        self.btn_auto = ttk.Button(controls, text='Auto-play',
                                   command=self.toggle_auto, width=10)
        self.btn_auto.pack(side='left', padx=4)
        self.strategy = tk.StringVar(value='balanced')
        strat = ttk.Combobox(controls, textvariable=self.strategy,
                             values=list(STRATEGIES), state='readonly', width=10)
        strat.pack(side='left', padx=4)
        strat.bind('<<ComboboxSelected>>', self.on_strategy)
        self.speed = tk.StringVar(value='4')
        speed = ttk.Combobox(controls, textvariable=self.speed,
                             values=['1', '4', '12', '60'], state='readonly',
                             width=3)
        speed.pack(side='left')
        speed.bind('<<ComboboxSelected>>', self.on_speed)
        ttk.Label(controls, text='steps/s').pack(side='left', padx=(2, 0))

        # Both wrap: a victory line, or a combat round's text, is long.
        self.prompt_title = tk.Label(right, font=('Arial', 12, 'bold'),
                                     wraplength=340, justify='left')
        self.prompt_title.pack(fill='x')
        self.prompt_body = tk.Label(right, font=('Arial', 9), wraplength=340,
                                    justify='left', anchor='w')
        self.prompt_body.pack(fill='x')
        self.buttons = ttk.Frame(right)
        self.buttons.pack(fill='x')

        self.map.draw(game)
        self.refresh_status()
        self.log_index = 0

    def redraw(self):
        self.map.show_grid = bool(self.show_grid.get())
        self.map.show_ids = bool(self.show_ids.get())
        self.map.show_traces = bool(self.show_traces.get())
        self.map.show_names = bool(self.show_names.get())
        self.map.draw(self.game)

    def on_zoom(self, _event=None):
        """Rescale the board (the canvas is scrolled by its container)."""
        self.map.set_scale(ZOOM[self.zoom.get()])
        self.map.draw(self.game)

    def on_map_mode(self, _event=None):
        self.map.mode = self.map_mode.get()
        self.map.draw(self.game)

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
        # Redrawing 460 hexes on every prompt makes autoplay crawl; the map
        # only changes when the party moves (or the day rolls over a new camp).
        marker = (g.hex, getattr(g, 'raft', False), len(g.party))
        if marker != getattr(self, '_drawn', None):
            self.map.draw(g)
            self._drawn = marker

    def drain_notes(self):
        for line in self.game.log[self.log_index:]:
            self.log_line(line)
        self.log_index = len(self.game.log)

    def log_line(self, text):
        self.log.insert('end', text + '\n')
        self.log.see('end')

    def ask(self, prompt, enabled=True):
        """Draw the prompt (title, text, buttons); a click resumes the loop.

        With ``enabled=False`` the buttons are shown but inert, which is what
        the player watches while the bot is playing: the panel always describes
        the prompt that is actually pending, never a stale one.
        """
        self.prompt_title.configure(text=prompt['title'])
        self.prompt_body.configure(text=prompt['text'])
        for w in self.buttons.winfo_children():
            w.destroy()
        for i, opt in enumerate(prompt['options']):
            button = tk.Button(self.buttons, text=opt['label'],
                               command=lambda i=i: self.answer(i))
            if not enabled:
                button.configure(state='disabled')
            button.pack(fill='x')

    def answer(self, index):
        if not self.game.prompts:
            return
        self.game.answer(index)
        self.schedule(0)

    # ------------------------------------------------------------ autoplay
    def on_strategy(self, _event=None):
        self.bot = Bot(self.game, self.strategy.get(), variety=0.3)
        self.log_line(f'Bot strategy: {self.strategy.get()}.')
        self.schedule(0)

    def on_speed(self, _event=None):
        try:
            steps = int(self.speed.get())
        except ValueError:
            steps = 4
        self.delay = max(16, int(1000 / max(1, steps)))

    def bot_move(self):
        """Answer the current prompt with the bot's choice."""
        g = self.game
        if g.game_over:
            return
        if not g.prompts:
            g.advance()
        if g.prompts:
            p = g.current()
            if p['kind'] == 'info' or not p['options']:
                self.log_line('>> ' + p['title'] + ': ' + p['text'])
                g.answer(0)
            else:
                g.answer(self.bot.choose(p))
        self.schedule(0)

    def toggle_auto(self):
        self.auto = not self.auto
        self.btn_auto.configure(text='Pause' if self.auto else 'Auto-play')
        self.log_line('Auto-play ' + ('on.' if self.auto else 'paused.'))
        self.schedule(0)

    def schedule(self, ms):
        # One pending tick at a time: a restart or a click during the wait must
        # not leave two loops running.
        if self._after is not None:
            try:
                self.root.after_cancel(self._after)
            except Exception:
                pass
        self._after = self.root.after(max(1, ms), self.tick)

    def restart(self):
        """Abandon this campaign and start a fresh one."""
        self.auto = False
        self.btn_auto.configure(text='Auto-play')
        self.game = Game()
        self.bot = Bot(self.game, self.strategy.get(), variety=0.3)
        self.log.delete('1.0', 'end')
        self.log_index = 0
        self._drawn = None
        self.prompt_title.configure(text='')
        self.prompt_body.configure(text='')
        for w in self.buttons.winfo_children():
            w.destroy()
        self.btn_auto.state(['!disabled'])
        self.btn_bot.state(['!disabled'])
        self.refresh_status()
        self.map.draw(self.game)
        self.log_line('*** New game - day 1 in hex ' + self.game.hex + '.')
        self.schedule(1)

    def tick(self):
        """One unit of work: advance the day, or settle the current prompt."""
        self._after = None
        g = self.game
        if g.game_over:
            self.finish()
            return
        self.drain_notes()
        self.refresh_status()
        if g.prompts:
            p = g.current()
            if p['kind'] == 'info' or not p['options']:
                self.log_line('>> ' + p['title'] + ': ' + p['text'])
                g.answer(0)
                self.schedule(0)
                return
            if self.auto:
                # Show the prompt the bot is answering (greyed out), so the
                # panel never keeps a previous prompt on screen.
                self.ask(p, enabled=False)
                # The bot plans a camp/mine route on its first decision and
                # again when the plan is exhausted, which can take a second or
                # two; say so instead of looking frozen.
                self.prompt_title.configure(text='Bot: ' + p['title'])
                self.root.update_idletasks()
                choice = self.bot.choose(p)
                g.answer(choice)
                self.schedule(self.delay)
                return
            self.ask(p)                      # wait for the player's click
            return
        g.advance()
        self.schedule(self.delay if self.auto else 1)

    def finish(self):
        g = self.game
        self.drain_notes()
        self.log_line('*** ' + (g.reason or 'Game over'))
        reason = g.reason or 'Game over'
        won = bool(getattr(g, 'won', False))
        self.prompt_title.configure(text='Victory!' if won else 'Game over')
        self.prompt_body.configure(text=reason)
        for w in self.buttons.winfo_children():
            w.destroy()
        tk.Button(self.buttons, text='Close',
                  command=self.root.destroy).pack(fill='x')
        self.btn_auto.state(['disabled'])
        self.btn_bot.state(['disabled'])

    def run(self):
        self.schedule(1)
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
