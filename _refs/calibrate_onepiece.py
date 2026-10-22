"""Recalibrate hex grid geometry for the one-piece scan.

The one-piece scan has a different aspect ratio than the original two scans,
so we need new R, x0, y0 values. Since the scan has some perspective
distortion (W/H ≈ 0.83 vs theoretical 0.766), we prioritize fitting the
height (23 rows) and accept some horizontal margin.

Outputs: new R, x0, y0 for geometry.py
"""
import math
import numpy as np
from PIL import Image

# ── Load the one-piece scan ──────────────────────────────────────────
im = Image.open('_refs/barbarianprince_onepiecemap-revc.jpg').convert('RGB')
A = np.asarray(im, dtype=np.float32)
H, W = A.shape[:2]
gray = A.mean(axis=2)

NC, NR = 20, 23  # grid dimensions

# ── Find content bounds ──────────────────────────────────────────────
# The board content is not pure white; threshold to find non-paper pixels
THRESH = 200
nonwhite = gray < THRESH
rows_c = np.where(nonwhite.any(axis=1))[0]
cols_c = np.where(nonwhite.any(axis=0))[0]
content_left = cols_c[0]
content_right = cols_c[-1]
content_top = rows_c[0]
content_bottom = rows_c[-1]
content_w = content_right - content_left + 1
content_h = content_bottom - content_top + 1

print(f"Image size: {W}x{H}")
print(f"Content bounds: x=[{content_left},{content_right}] y=[{content_top},{content_bottom}]")
print(f"Content size: {content_w}x{content_h}  ratio={content_w/content_h:.4f}")
print(f"Theoretical 20x23 ratio: {30.5/(math.sqrt(3)*NR):.4f}")
print()

# ── Compute R ────────────────────────────────────────────────────────
# Width-based R: content_w = 30.5 * R
R_w = content_w / 30.5
# Height-based R: content_h = sqrt(3) * R * NR
R_h = content_h / (math.sqrt(3) * NR)
print(f"R from width:  {R_w:.2f}")
print(f"R from height: {R_h:.2f}")
print(f"Ratio differs by {(R_w/R_h - 1)*100:.1f}% -> perspective distortion present")
print()

# Prioritize height (tighter constraint, less overhang)
# Round to a clean value
R = round(R_h * 10) / 10
print(f"Chosen R = {R}")
print()

# ── Compute DX, DY ───────────────────────────────────────────────────
DX = 1.5 * R
DY = math.sqrt(3) * R

# ── Compute board extents with chosen R ──────────────────────────────
board_w = 30.5 * R
board_h = math.sqrt(3) * R * NR

# Anchor top-left of board at content bounds
# For flat-top hexes:
#   Left vertex of col 1 = x0 - R
#   Top vertex of row 1  = y0 - sqrt(3)*R/2
x0 = content_left + R
y0 = content_top + math.sqrt(3) * R / 2

board_minx = x0 - R          # = content_left
board_maxx = x0 - R + board_w
board_miny = y0 - math.sqrt(3)*R/2  # = content_top
board_maxy = y0 - math.sqrt(3)*R/2 + board_h

print("=== Calibration results ===")
print(f"R  = {R}")
print(f"DX = {DX:.4f}")
print(f"DY = {DY:.4f}")
print(f"x0 = {x0:.4f}")
print(f"y0 = {y0:.4f}")
print()
print(f"Board extents: x=[{board_minx:.1f}, {board_maxx:.1f}]  width={board_w:.1f}")
print(f"              y=[{board_miny:.1f}, {board_maxy:.1f}]  height={board_h:.1f}")
print()
print(f"Content extents: x=[{content_left}, {content_right}]  width={content_w}")
print(f"                y=[{content_top}, {content_bottom}]  height={content_h}")
print()

# ── Verify all hexes fit within the image ────────────────────────────
def hex_centre(col, row):
    i = col - 1
    cx = x0 + DX * i
    cy = y0 + DY * (row - 1) + (i % 2) * DY / 2.0
    return cx, cy

def hex_corners(col, row):
    cx, cy = hex_centre(col, row)
    angles = range(0, 360, 60)
    return [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
            for a in angles]

out_of_bounds = 0
for col in range(1, NC + 1):
    for row in range(1, NR + 1):
        for cx, cy in hex_corners(col, row):
            if cx < 0 or cx >= W or cy < 0 or cy >= H:
                out_of_bounds += 1
                print(f"  WARN: hex {col:02d}{row:02d} corner ({cx:.0f},{cy:.0f}) outside image")

if out_of_bounds == 0:
    print("All 460 hexes fit within the image bounds.")
else:
    print(f"{out_of_bounds} corners outside bounds - adjustment needed")

# ── Corner hex positions for verification ───────────────────────────
print()
print("Corner hex centres:")
for c, r in [(1,1), (20,1), (1,23), (20,23)]:
    cx, cy = hex_centre(c, r)
    print(f"  Hex {c:02d}{r:02d}: ({cx:.1f}, {cy:.1f})")

# ── Sample hex centres for visual check ─────────────────────────────
print()
print("Sample hex centres (every 5th row):")
for row in range(1, NR+1, 5):
    for col in range(1, NC+1, 5):
        cx, cy = hex_centre(col, row)
        print(f"  Hex {col:02d}{row:02d}: ({cx:.0f}, {cy:.0f})", end="")
    print()

# ── Write summary for geometry.py ───────────────────────────────────
print()
print("=== For geometry.py ===")
print(f"R = {R}")
print(f"SCANS = {{")
print(f"    'barbarianprince_onepiecemap-revc.jpg': {{'x0': {x0:.4f}, 'y0': {y0:.4f}, 'first_row': 1, 'last_row': {NR}}},")
print(f"}}")
print(f"board_bounds should be ~({board_minx:.1f}, {board_miny:.1f}, {board_maxx:.1f}, {board_maxy:.1f})")
