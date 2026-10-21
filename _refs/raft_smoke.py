"""Smoke run: play a full campaign and report which days offered rafting."""
import sys

sys.path.insert(0, "src")
from engine import Game
from autoplay import Bot

g = Game(seed=42)
bot = Bot(g, "balanced")
menus = []
for _ in range(600):
    g.advance()
    if not g.prompts or g.game_over:
        break
    p = g.current()
    labels = [o["label"] for o in p["options"]]
    if "action in hex" in p["title"]:
        menus.append((g.day, g.hex, any("raft" in l.lower() for l in labels)))
    idx = bot.choose(p)
    g.answer(idx)

print("days:", g.day, "over:", g.game_over, "reason:", g.reason)
print("menus with raft:", [m for m in menus if m[2]])
print("menus without raft:", len([m for m in menus if not m[2]]))
print("raft days:", g.raft_days)
