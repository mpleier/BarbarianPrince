"""Barbarian Prince - browser front-end for the rules engine.

Run:
    python src/web.py                      # then open http://127.0.0.1:8000
    python src/web.py --port 8080 --seed 42

The engine is stateful and synchronous, so the server keeps one ``engine.Game``
per browser session and exposes a small JSON API.  The page in web/ draws the
20x23 board as SVG and answers the engine's prompt queue with buttons - or by
clicking a highlighted hex on the map.
"""
import argparse
import os
import re
import sys
import threading
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image

from engine import Game, split_event

# How much a campaign may drift from its personality (see autoplay.Bot).
VARIETY = 0.3
from autoplay import Bot, STRATEGIES
from features import load_features
from game_model import GameModel
from geometry import (NC, NR, R, DX, DY, board_bounds, board_corners,
                      board_xy, hex_id)
from map_scan import scan_image, scan_rect, original_scan_path

from resource import WEB

WEB_DIR = WEB

MODEL = GameModel.load()
FEATURES = load_features()
SESSIONS = {}
LOCK = threading.Lock()
HEX_RE = re.compile(r"->\s*(\d{4})")

app = FastAPI(title="Barbarian Prince (web)")


# ----------------------------------------------------------------- board data
def board_scan_rect():
    """Return (x, y, w, h) for the scan image.

    The scan is already in the geometry's pixel frame, so the image sits at
    the origin: the hex lattice includes the column zigzag, which is what the
    artwork shows.  The SVG viewBox clips to the board area so the margins
    are hidden automatically."""
    from map_scan import SCAN_SOURCE
    if not os.path.exists(SCAN_SOURCE):
        return None
    img = Image.open(SCAN_SOURCE)
    w, h = img.size
    return [0, 0, w, h]


def build_board():
    minx, miny, maxx, maxy = board_bounds()

    # The photograph is cropped inside the printed border, so the fitted
    # lattice runs a few pixels past the artwork; clip the view to the scan.
    rect = board_scan_rect()
    if rect:
        minx = max(minx, rect[0])
        miny = max(miny, rect[1])
        maxx = min(maxx, rect[0] + rect[2])
        maxy = min(maxy, rect[1] + rect[3])

    hexes = []
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            hid = hex_id(col, row)
            g = MODEL.grid[hid]
            cx, cy = board_xy(col, row)
            hexes.append({
                "id": hid,
                "col": col,
                "row": row,
                "terrain": g["terrain"],
                "travel_terrain": g["travel_terrain"],
                "confidence": g.get("confidence"),
                "cx": round(cx, 2),
                "cy": round(cy, 2),
                "points": [[round(x, 2), round(y, 2)]
                           for x, y in board_corners(col, row)],
                "neighbors": g["neighbors"],
                "place": FEATURES["places"].get(hid),
                "region": FEATURES["regions"].get(hid),
            })
    return {
        "minx": round(minx, 2), "miny": round(miny, 2),
        "maxx": round(maxx, 2), "maxy": round(maxy, 2),
        "radius": R, "dx": DX, "dy": DY,
        "hexes": hexes,
        "roads": [list(p) for p in FEATURES["road_sides"]],
        "rivers": [list(p) for p in FEATURES["river_sides"]],
        "road_hexes": FEATURES["road_hexes"],
        "terrain_colors": FEATURES["terrain_colors"],
        "scan": board_scan_rect(),
    }


# ------------------------------------------------------------------- sessions
class NewGame(BaseModel):
    seed: int | None = None
    start: str = "0101"
    strategy: str = "balanced"


class Answer(BaseModel):
    index: int


class Auto(BaseModel):
    steps: int = 40
    strategy: str | None = None


class Step(BaseModel):
    strategy: str | None = None


class Strategy(BaseModel):
    strategy: str


def ensure_prompt(g):
    """Advance the state machine until a prompt the player must answer exists."""
    while True:
        if g.game_over:
            return None
        g.advance()
        p = g.current()
        if p is None:
            continue
        if p["kind"] == "info" or not p["options"]:
            g.answer(0)
            continue
        return p


def get_session(sid):
    sess = SESSIONS.get(sid)
    if not sess:
        raise HTTPException(status_code=404, detail="no such game session")
    return sess


def snapshot(sess, full_log=False):
    g = sess["game"]
    prompt = ensure_prompt(g)
    options = []
    for opt in (prompt["options"] if prompt else []):
        m = HEX_RE.search(opt["label"])
        options.append({"label": opt["label"], "hex": m.group(1) if m else None})

    moves = []
    if prompt and prompt["kind"] == "choice" and prompt["title"].startswith("Move"):
        moves = [o["hex"] for o in options if o["hex"]]

    log = g.log if full_log else g.log[sess["log_index"]:]
    sess["log_index"] = len(g.log)

    bot_choice = None
    if prompt and prompt["options"]:
        try:
            bot_choice = sess["bot"].suggest(prompt)
            bot_choice = max(0, min(int(bot_choice), len(prompt["options"]) - 1))
        except Exception:
            bot_choice = None

    st = g.status()
    st["moves_left"] = g.moves_left
    st["speed"] = g.speed()
    st["phase"] = g.phase
    st["action"] = g.action
    # Richer combat snapshot (mirrors what the Tk GUI refresh_status shows)
    if g.combat:
        st["combat"] = {
            "name": g.combat.name,
            "round": g.combat.round,
            "party": [{"name": u.name, "hp": u.endurance - u.wounds,
                       "max": u.endurance, "dead": u.dead}
                      for u in g.combat.party],
            "foes": [{"name": u.name, "hp": u.endurance - u.wounds,
                      "max": u.endurance, "dead": u.dead}
                     for u in g.combat.foes],
        }
    else:
        st["combat"] = False
    st["visited"] = sorted(g.visited)
    st["raft"] = g.raft

    return {
        "session": sess["id"],
        "status": st,
        "prompt": None if prompt is None else {
            "kind": prompt["kind"],
            "title": prompt["title"],
            "text": prompt["text"],
            "options": options,
            "bot_choice": bot_choice,
        },
        "moves": moves,
        "strategy": sess["strategy"],
        "log": log,
        "log_count": len(g.log),
    }


BOARD = build_board()

# --------------------------------------------------------------------- routes
@app.get("/api/health")
def health():
    return {"ok": True, "hexes": len(BOARD["hexes"]), "sessions": len(SESSIONS),
            "strategies": list(STRATEGIES)}


@app.get("/api/board")
def api_board():
    return BOARD


@app.post("/api/game")
def api_new_game(req: NewGame):
    with LOCK:
        strategy = req.strategy if req.strategy in STRATEGIES else "balanced"
        g = Game(seed=req.seed, start_hex=req.start)
        sess = {"id": uuid.uuid4().hex[:12], "game": g, "log_index": 0,
                "strategy": strategy, "bot": Bot(g, strategy, variety=VARIETY)}
        SESSIONS[sess["id"]] = sess
        return snapshot(sess)


@app.get("/api/game/{sid}")
def api_game(sid: str):
    with LOCK:
        sess = get_session(sid)
        sess["log_index"] = 0
        return snapshot(sess, full_log=True)


@app.post("/api/game/{sid}/answer")
def api_answer(sid: str, req: Answer):
    with LOCK:
        sess = get_session(sid)
        g = sess["game"]
        prompt = ensure_prompt(g)
        if prompt is None:
            return snapshot(sess)
        if not 0 <= req.index < len(prompt["options"]):
            raise HTTPException(status_code=400, detail="invalid choice")
        try:
            g.answer(req.index)
        except Exception as exc:                      # keep the UI alive
            g.note(f"(engine error while resolving the choice: {exc})")
        return snapshot(sess)


@app.post("/api/game/{sid}/step")
def api_step(sid: str, req: Step):
    """Answer the current prompt with the bot's best move - one step only."""
    with LOCK:
        sess = get_session(sid)
        g = sess["game"]
        if req.strategy and req.strategy in STRATEGIES:
            sess["strategy"] = req.strategy
            sess["bot"] = Bot(g, req.strategy, variety=VARIETY)
        prompt = ensure_prompt(g)
        if prompt is None:
            return snapshot(sess)
        try:
            idx = sess["bot"].choose(prompt)
            idx = max(0, min(int(idx), len(prompt["options"]) - 1))
            g.answer(idx)
        except Exception as exc:                      # keep the UI alive
            g.note(f"(engine error while resolving the bot's choice: {exc})")
        return snapshot(sess)


@app.post("/api/game/{sid}/strategy")
def api_strategy(sid: str, req: Strategy):
    """Switch the bot's personality mid-game (its memory starts fresh)."""
    with LOCK:
        sess = get_session(sid)
        if req.strategy not in STRATEGIES:
            raise HTTPException(status_code=400,
                                detail="strategy must be one of " +
                                       ", ".join(STRATEGIES))
        sess["strategy"] = req.strategy
        sess["bot"] = Bot(sess["game"], req.strategy, variety=VARIETY)
        return snapshot(sess)


@app.post("/api/game/{sid}/auto")
def api_auto(sid: str, req: Auto):
    """Run the bot for a number of prompts.

    strategy="naive" answers every prompt with the first option, which is useful
    for engine smoke tests; otherwise the personality bot plays the game.
    """
    with LOCK:
        sess = get_session(sid)
        g = sess["game"]
        if req.strategy and req.strategy in STRATEGIES:
            sess["strategy"] = req.strategy
            sess["bot"] = Bot(g, req.strategy, variety=VARIETY)
        chooser = None if req.strategy == "naive" else sess["bot"].choose
        g.run_until_idle(max_steps=req.steps, chooser=chooser)
        return snapshot(sess)


def _ref_options(code, text):
    """The event's option matrix as a table, or None.

    The curated table in data/event_options.json wins; otherwise the matrix is
    pulled out of the printed text, so the reference window never shows a run-on
    "... die roll Negotiate * evade fight 1 surprised r308 ..." paragraph.
    """
    curated = MODEL.event_options(code)
    _prose, parsed = split_event(text)
    if curated:
        return {
            "headers": curated["columns"],
            "rolls": [row["roll"] for row in curated["rows"]],
            "rows": [[{"label": cell.get("label", ""), "ref": cell.get("ref")}
                      for cell in row["cells"]] for row in curated["rows"]],
            "note": (parsed or {}).get("note", ""),
        }
    if parsed:
        return {
            "headers": parsed["headers"],
            "rolls": [roll for roll, _cells in parsed["rows"]],
            "rows": [[{"label": label, "ref": ref} for label, ref in cells]
                     for _roll, cells in parsed["rows"]],
            "note": parsed["note"],
        }
    return None


@app.get("/api/ref/{ref}")
def api_ref(ref: str):
    ref = ref.lower()
    if ref in MODEL.rules:
        r = MODEL.rules[ref]
        return {"id": r["id"], "title": r.get("title", ""), "text": r.get("text", ""),
                "options": None}
    if ref in MODEL.events:
        e = MODEL.events[ref]
        text = e.get("text", "")
        prose, _parsed = split_event(text)
        return {"id": e.get("code", ref), "title": e.get("title", ""), "text": prose,
                "options": _ref_options(ref, text)}
    raise HTTPException(status_code=404, detail=f"no rule or event {ref}")


@app.get("/api/hex/{hid}")
def api_hex(hid: str):
    hid = hid.zfill(4)
    if hid not in MODEL.grid:
        raise HTTPException(status_code=404, detail="no such hex")
    h = MODEL.grid[hid]
    return {
        "id": hid,
        "terrain": h["terrain"],
        "travel_terrain": h["travel_terrain"],
        "place": FEATURES["places"].get(hid),
        "region": FEATURES["regions"].get(hid),
        "neighbors": h["neighbors"],
        "events": MODEL.index.get("hex_events", {}).get(hid, []),
        "on_road": hid in FEATURES["road_hexes"],
    }


@app.get("/scan/board.jpg")
def api_scan():
    """Serve the original full-resolution scan so hex coordinates align
    perfectly with the geometry-calibrated centers."""
    path = original_scan_path()
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="board scan not available")
    return FileResponse(
        path, media_type="image/jpeg",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )

app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="ui")



def serve(port=0, host="127.0.0.1", seed=None, open_browser=True, window=False):
    """Run the web game, optionally on a free port, and open the browser.

    Returns the port actually bound, which matters for the packaged exe: it
    asks the OS for a free port so it does not collide with whatever else the
    player is running.  ``window=True`` keeps a small Tk window open while the
    server runs, so a windowed build has a visible "Quit" button.
    """
    import socket
    import threading
    import webbrowser

    import uvicorn

    if port == 0:
        with socket.socket() as probe:
            probe.bind((host, 0))
            port = probe.getsockname()[1]
    url = f"http://{host}:{port}/"
    print(f"Barbarian Prince -> {url}  (seed {seed})", flush=True)
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    if window:
        return _serve_with_window(url, host, port)

    uvicorn.run(app, host=host, port=port, log_level="warning")
    return port


def _serve_with_window(url, host, port):
    """Serve in a thread and show a tiny control window (packaged build)."""
    import os
    import threading
    import webbrowser

    import tkinter as tk

    import uvicorn

    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port,
                                           log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()

    root = tk.Tk()
    root.title("Barbarian Prince")
    root.resizable(False, False)
    frame = tk.Frame(root, padx=18, pady=14)
    frame.pack(fill="both", expand=True)
    tk.Label(frame, text="The game is running in your browser:",
             anchor="w").pack(fill="x")
    link = tk.Label(frame, text=url, fg="#1a4f8a", cursor="hand2")
    link.pack(anchor="w", pady=(2, 12))

    def open_tab():
        webbrowser.open(url)

    link.bind("<Button-1>", lambda _e: open_tab())
    buttons = tk.Frame(frame)
    buttons.pack(fill="x")
    tk.Button(buttons, text="Open browser", command=open_tab,
              width=14).pack(side="left")
    tk.Button(buttons, text="Quit", command=lambda: (server.should_exit,
                                                     root.destroy()),
              width=10).pack(side="right")

    def on_close():
        server.should_exit = True
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    server.should_exit = True
    return port


def main():
    ap = argparse.ArgumentParser(description="Barbarian Prince web game")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    serve(port=args.port, host=args.host, seed=args.seed, open_browser=False)


if __name__ == "__main__":
    main()

