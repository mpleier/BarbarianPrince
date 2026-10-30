# BarbarianPrince — game model

A machine-readable model of the 1981 *BarbarianPrince* board game, built from the
rule booklet, the events sheet, the errata sheet and the map scan.

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1 | `_refs/clean_rules.py`, `_refs/clean_tables.py`, `_refs/extract_events2.py` | `_refs/rules_clean.txt`, `_refs/tables_clean.txt`, `_refs/events_clean.txt` |
| 2 | `_refs/map_model.py` | `_refs/hexes.json` — 460 hexes with terrain + classification distance |
| 3 | `_refs/rectify_scan.py` | `_refs/BPMap_rectified.jpg` — the photograph with its perspective removed |
| 4 | `src/geometry.py` | (imported) authoritative hex geometry: centres, neighbours, terrain map |
| 5 | `src/features.py` | `data/features.json` — river/road sides traced from the rectified scan |
| 6 | `_refs/extract_tables.py` | `data/rules.json`, `data/tables.json` |
| 7 | `_refs/extract_events2.py` | `data/events.json`, `data/event_options.json` |
| 8 | `src/build_model.py` | `data/game_model.json`, `data/validation_report.txt` |

Run the whole thing with:

```powershell
python _refs/rectify_scan.py
python _refs/extract_tables.py
python src/features.py
python src/build_model.py
python -m unittest discover -s tests
```

## Playing it

| Interface | Command |
|---|---|
| Browser (web GUI) | `python src/web.py` then open http://127.0.0.1:8000 |
| Browser, free port | `python src/main.py --web` (opens a tab) |
| Tkinter desktop | `python src/main.py` |
| Terminal | `python src/main.py --cli` |
| Auto-play (no input) | `python src/main.py --auto --seed 42` |

Both graphical front ends can hand the game to the bot: the Tk window has
**New game** (abandon the campaign and start a fresh one), **Bot move** (answer
the current prompt) and **Auto-play** (play on, with a 1/4/12/60
steps-per-second setting and a strategy picker), and the browser page has the
same buttons in its toolbar.  `python _refs/gui_smoke.py 10` opens the
Tk window, lets the bot play for ten seconds and checks the loop, the manual
answers and the end screen.

## Autoplay personalities

Eight personalities, all sharing one scoring engine — they differ only in
appetites (travel, rest, news, hire, audience, ruins, raft, fight, flee, talk,
caution, gold buffer, party size):

| Strategy | Plays like |
|---|---|
| `cautious` | avoids fights, keeps a 30-gold buffer, rests when hurt |
| `balanced` | the default: sensible travel, opportunistic fighting |
| `aggressive` | seeks battle, hires a big party, spends freely |
| `explorer` | covers ground, keeps the party small, loves the river |
| `merchant` | mines ruins hard and hoards gold |
| `zealot` | lives at the temples for audiences and offerings |
| `daredevil` | fights everything, never flees, no gold buffer |
| `wanderer` | drifts: travel first, little interest in hiring |

`variety` (0 – 1) lets a run drift from its personality, so two campaigns with
the same strategy do not play out identically: the weights wobble per campaign,
near-equal options are taken at random, and from 0.2 the party commits to a
different ruin/temple route whenever two are within a whisker of each other (the
board has three ruins, and the top two are often one day apart).  The bot also
stops flogging a dead mine: a ruin that pays nothing for four days is abandoned
for another, and the daily action scores decay with repetition, so an autoplay
campaign alternates mining, travel, rest and markets instead of searching the
same ruins for the whole game.  Measured over 40 seeds with `balanced` at 0.3:
ruin target **0307 on 17 campaigns, 0801 on 23**, mean 23 distinct hexes per
campaign, longest same-action run down from 29 days to 17.

| variety | wins | distinct ending hexes |
|---|---|---|
| 0.0 | 5/60 | 6 |
| 0.3 (default) | 5/60 | 8 |
| 0.6 | 2/60 | 11 |

`--variety` sets it from the command line; `--variety 0` restores a fully
deterministic run (same seed → same game).

The web front-end (`src/web.py` + `web/`) needs FastAPI and uvicorn
(`pip install fastapi uvicorn`).  It serves an SVG of the 20x23 board - terrain
fills, roads, rivers, named places - plus the party status, the prompt panel
and the adventure log.  The toolbar's **Map style** dropdown switches between
flat terrain fills, the original board artwork (`_refs/BPMap.jpg`, served at
`/scan/board.jpg`) and a blend of the two; **rivers & roads** toggles the
traced feature lines.  One `engine.Game` is kept per browser session, so
several tabs can run independent games.  Two smoke tests drive it end to end:

```powershell
python _refs/web_smoke.py --port 8000   # API: board, game start, answers
node  _refs/js_smoke.mjs  http://127.0.0.1:8000   # app.js against a DOM shim
```

## Windows build

`python build_exe.py` builds **`dist\BarbarianPrince\`** — a portable folder with
`BarbarianPrince.exe` and an `_internal\` directory.  Copy the folder anywhere
and double-click the exe; no installer, no Python, and **no temporary
directory**: the exe loads its libraries and data from `_internal\` in place.

| Launch | What happens |
|---|---|
| double-click | Tk window: board (place names and four sizes), party, log, prompts, bot controls |
| `BarbarianPrince.exe --web` | local server on a free port, browser tab opens, and a small window stays open with **Quit** |
| `BarbarianPrince.exe --web --no-browser --port 8157` | headless server (for scripts) |
| `BarbarianPrince.exe --auto --seed 42` | bot plays a campaign; output goes nowhere, so use the source for logs |

`python build_exe.py --onefile` still produces a single `dist\BarbarianPrince.exe`
(~43 MB) for people who want one file to pass around — that variant unpacks
itself into `%TEMP%` on every run, which the folder build avoids.

`bp.spec` bundles `data/` (the model), `web/` (browser UI) and
`_refs/BPMap_rectified.jpg` (the "original artwork" map view).  scipy is
excluded: it is only needed to re-trace rivers and roads from the scan, which
the shipped game never does — it reads `data/features.json`.  `src/resource.py`
resolves those paths for both a checkout and a frozen bundle, and the board
artwork is turned into a Tk image in memory (`PIL.ImageTk`), so nothing is
written to disk at all; only the web view's downscaled scan cache lands under
`%LOCALAPPDATA%\BarbarianPrince`.

If `pip install pyinstaller` is unavailable, `python _fetch_pyinstaller.py`
downloads the wheels from PyPI into `._vendor/`; then run

```powershell
$env:PYTHONPATH = "$PWD\._vendor"
python build_exe.py
```

## Geometry

The board is a 20-column x 23-row hex grid (460 hexes), **flat-top** hexes.
Hex `colrow` is zero-padded, e.g. `1212` = column 12, row 12.

With `i = col - 1`, `j = row - 1` and `R = 79.05 px`:

```
centre(col, row) = (X0 + 1.5*R*i, Y0 + sqrt(3)*R*j + (sqrt(3)*R/2 if col is even))
corners          = centre + (R*cos(a), R*sin(a))  for a in 0..300 step 60
```

The lattice is calibrated on `_refs/BPMap_rectified.jpg`, the photograph with
its keystone removed by `_refs/rectify_scan.py` (a homography fitted to the
printed borders at 42 hexes).  On the raw photograph the printed grid drifts by
up to 30 px across the image and has to be fitted as a 1.6 % taller-than-wide
lattice; after rectification a regular lattice sits within **0.98 px** of the
printed borders on average.

Even columns sit half a row lower than odd columns, so the east/west neighbours
of an odd column are one row higher than those of the even column beside it.
The scan is cropped just inside the printed border, so the outer row runs a few
pixels past the artwork; the web view clips to the scan, which is why the outer
row looks cut just like the photograph.

## Model schema (`data/game_model.json`)

```
meta            - counts and provenance
geometry        - orientation, radius, dx/dy, scan offsets
grid            - 460 entries: id, col, row, terrain, travel_terrain,
                  neighbours, centre_px, confidence
rules           - r201..r343 sections (69) with title + text
tables          - travel table, combat table, treasure, news, hiring, offerings,
                  audience, raft travel, traps, cache recovery, errata, ...
events          - e001..e195 (182; e167-e179 do not exist in the booklet)
event_options   - 22 encounter option matrices
index           - reverse index of every rNNN/eNNN reference, hex->event map,
                  dangling refs, corrected misprints
```

## Known data issues

* Terrain classification is colour-based; 5 hexes have confidence < 0.4 and
  should be eyeballed against the map.
* The booklet misprints five section references; `index.reference_fixes` maps
  them to the intended sections (`e226->e026`, `e250->e050`, `e341->r341`,
  `r119->r319`, `r143->r341`).
* `r229` and `r282-r299` genuinely do not exist.
* `e001`, `e119` and `e157` are never referenced by any other section.
* River and road sides are traced from the scan by ink colour and shape, then
  scored by how much of each hex edge the drawn line covers.  Every side in
  `features.json` therefore joins two adjacent hexes (the earlier pixel-link
  detector produced 39 river and 4 road sides between hexes that do not
  touch).  Faint sides that would join two pieces of the same feature, or
  reach the edge of the board, are filled in afterwards, and isolated sides
  are dropped unless the ink is strong; that removes most ridge-shading false
  positives.  Rivers drawn across hex interiors still cannot be expressed as
  sides, and short road stretches through hex interiors are likewise missing
  from `road_sides` (they are covered by `road_hexes`).
* The colour-corrected scan (`_refs/barbarianprince_onepiecemap-revc.jpg`,
  wider page with the map key) is still the raw keystoned photograph, so it
  keeps its own unrectified lattice in `features.CALIB_REVC`; the rectified
  BPMap scan is the default for tracing.
