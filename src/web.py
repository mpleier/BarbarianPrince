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

from engine import Game
from features import load_features
from game_model import GameModel
from geometry import (NC, NR, R, DX, DY, BOARD_Y_OFF, board_bounds, board_corners,
                      board_xy, hex_id)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")
STITCH = os.path.join(ROOT, "_refs", "board_stitch.png")

MODEL = GameModel.load()
FEATURES = load_features()
SESSIONS = {}
LOCK = threading.Lock()
HEX_RE = re.compile(r"->\s*(\d{4})")

app = FastAPI(title="Barbarian Prince (web)")


# ----------------------------------------------------------------- board data
def scan_rect():
    """Rectangle (x, y, w, h) in unified scan pixels covered by the stitched
    board image, so the scan can be used as a map underlay."""
    try:
        from PIL import Image
        w1, h1 = Image.open(os.path.join(ROOT, "_refs", "map1.jpg")).size
        w2, h2 = Image.open(os.path.join(ROOT, "_refs", "map2.jpg")).size
    except Exception:
        return None
    if not os.path.exists(STITCH):
        return None
    w = max(w1, w2)
    h = int(max(h1 + BOARD_Y_OFF["map1.jpg"], h2 + BOARD_Y_OFF["map2.jpg"])) + 20
    return [0, 0, w, h]


def build_board():
    minx, miny, maxx, maxy = board_bounds()
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
        "scan": scan_rect(),
    }


# ------------------------------------------------------------------- sessions
class NewGame(BaseModel):
    seed: int | None = None
    start: str = "0101"


class Answer(BaseModel):
    index: int


class Auto(BaseModel):
    steps: int = 40


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

    st = g.status()
    st["moves_left"] = g.moves_left
    st["speed"] = g.speed()
    st["phase"] = g.phase
    st["action"] = g.action
    st["combat"] = bool(g.combat)
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
        },
        "moves": moves,
        "log": log,
        "log_count": len(g.log),
    }


BOARD = build_board()

# --------------------------------------------------------------------- routes
@app.get("/api/health")
def health():
    return {"ok": True, "hexes": len(BOARD["hexes"]), "sessions": len(SESSIONS)}


@app.get("/api/board")
def api_board():
    return BOARD


@app.post("/api/game")
def api_new_game(req: NewGame):
    with LOCK:
        g = Game(seed=req.seed, start_hex=req.start)
        sess = {"id": uuid.uuid4().hex[:12], "game": g, "log_index": 0}
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


@app.post("/api/game/{sid}/auto")
def api_auto(sid: str, req: Auto):
    """Answer prompts with the first option - handy for demos and testing."""
    with LOCK:
        sess = get_session(sid)
        sess["game"].run_until_idle(max_steps=req.steps)
        return snapshot(sess)


@app.get("/api/ref/{ref}")
def api_ref(ref: str):
    ref = ref.lower()
    if ref in MODEL.rules:
        r = MODEL.rules[ref]
        return {"id": r["id"], "title": r.get("title", ""), "text": r.get("text", "")}
    if ref in MODEL.events:
        e = MODEL.events[ref]
        return {"id": e["id"], "title": e.get("title", ""), "text": e.get("text", "")}
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


@app.get("/scan/board.png")
def api_scan():
    if not os.path.exists(STITCH):
        raise HTTPException(status_code=404, detail="board scan not generated")
    return FileResponse(STITCH, media_type="image/png")

app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="ui")



def main():
    ap = argparse.ArgumentParser(description="Barbarian Prince web game")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    import uvicorn
    print(f"Barbarian Prince -> http://{args.host}:{args.port}  (seed {args.seed})")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="ui")

