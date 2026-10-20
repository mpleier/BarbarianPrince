# BarbarianPrince â€” game model

A machine-readable model of the 1981 *BarbarianPrince* board game, built from the
rule booklet, the events sheet, the errata sheet and the three map scans.

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1 | `_refs/clean_rules.py`, `_refs/clean_tables.py`, `_refs/extract_events2.py` | `_refs/rules_clean.txt`, `_refs/tables_clean.txt`, `_refs/events_clean.txt` |
| 2 | `_refs/map_model.py` | `_refs/hexes.json` â€” 460 hexes with terrain + classification distance |
| 3 | `src/geometry.py` | (imported) authoritative hex geometry: centres, neighbours, terrain map |
| 4 | `_refs/extract_tables.py` | `data/rules.json`, `data/tables.json` |
| 5 | `_refs/extract_events2.py` | `data/events.json`, `data/event_options.json` |
| 6 | `src/build_model.py` | `data/game_model.json`, `data/validation_report.txt` |

Run the whole thing with:

```powershell
python _refs/extract_tables.py
python src/build_model.py
python -m unittest discover -s tests
```

## Playing it

| Interface | Command |
|---|---|
| Browser (web GUI) | `python src/web.py` then open http://127.0.0.1:8000 |
| Tkinter desktop | `python src/main.py` |
| Terminal | `python src/main.py --cli` |
| Auto-play (no input) | `python src/main.py --auto --seed 42` |

The web front-end (`src/web.py` + `web/`) needs FastAPI and uvicorn
(`pip install fastapi uvicorn`).  It serves an SVG of the 20x23 board - terrain
fills, roads, rivers, named places, optional scan underlay - plus the party
status, the prompt panel and the adventure log.  One `engine.Game` is kept per
browser session, so several tabs can run independent games.  Two smoke tests
drive it end to end:

```powershell
python _refs/web_smoke.py --port 8000   # API: board, game start, answers
node  _refs/js_smoke.mjs  http://127.0.0.1:8000   # app.js against a DOM shim
```

## Geometry

The board is a 20-column x 23-row hex grid (460 hexes), **flat-top** hexes.
Hex `colrow` is zero-padded, e.g. `1212` = column 12, row 12.

With `i = col - 1`, `j = row - 1` and `R = 106.0 px`:

```
centre(col, row) = (X0 + 1.5*R*i, Y0 + sqrt(3)*R*j + (i % 2) * sqrt(3)*R/2)
```

Even columns sit half a row higher than odd columns, so the east/west neighbours
shift by one row depending on the parity of `i`. Adjacent hex centres are
`sqrt(3) * R` apart, which is what the map scans confirm.

