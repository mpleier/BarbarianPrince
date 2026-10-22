"""Generate a visual hex grid with model rivers/roads for comparison."""
import json, os, math
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'data')

with open(os.path.join(DATA, 'features.json'), encoding='utf-8') as f:
    feats = json.load(f)

NC, NR = 20, 23
R = 55.0
SQ3 = math.sqrt(3.0)
DX = 1.5 * R
DY = SQ3 * R

def parse_hex(hid):
    return int(hid[:2]), int(hid[2:])

def hex_centre(col, row):
    i = col - 1
    return (DX * i, DY * (row - 1) + (i % 2) * DY / 2.0)

def hex_corners(col, row):
    cx, cy = hex_centre(col, row)
    return [(cx + R * math.cos(math.radians(a)),
             cy + R * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]

def neighbours(col, row):
    i, j = col - 1, row - 1
    if i % 2 == 0:
        pairs = {'NE': (i+1, j-1), 'SE': (i+1, j),
                 'NW': (i-1, j-1), 'SW': (i-1, j)}
    else:
        pairs = {'NE': (i+1, j), 'SE': (i+1, j+1),
                 'NW': (i-1, j), 'SW': (i-1, j+1)}
    pairs['N'] = (i, j-1); pairs['S'] = (i, j+1)
    out = {}
    for name, (ni, nj) in pairs.items():
        ni += 1; nj += 1
        if 1 <= ni <= NC and 1 <= nj <= NR:
            out[name] = f'{ni:02d}{nj:02d}'
    return out

# Bounds
all_c = []
for col in range(1, NC+1):
    for row in range(1, NR+1):
        all_c.extend(hex_corners(col, row))
minx = min(c[0] for c in all_c) - 15
miny = min(c[1] for c in all_c) - 15
board_w = max(c[0] for c in all_c) - minx + 15
board_h = max(c[1] for c in all_c) - miny + 15

margin = 90
W = int(board_w) + margin
H = int(board_h) + 50

canvas = Image.new('RGB', (W, H), (240, 240, 235))
draw = ImageDraw.Draw(canvas)

# Draw terrain fills (simplified - all light green)
for col in range(1, NC+1):
    for row in range(1, NR+1):
        pts = [(x - minx + margin//2, y - miny + 35)
               for x, y in hex_corners(col, row)]
        draw.polygon(pts, fill=(210, 225, 190), outline=(180, 180, 170), width=1)

# River sides modelled (magenta lines)
river_sides = [frozenset(p) for p in feats['river_sides']]
road_sides = [frozenset(p) for p in feats['road_sides']]

def draw_side_edge(a, b, color, width):
    col_a, row_a = parse_hex(sorted(a)[0])
    col_b, row_b = parse_hex(sorted(a)[-1])
    ca_pts = [(x - minx + margin//2, y - miny + 35)
              for x, y in hex_corners(col_a, row_a)]
    cb_pts = [(x - minx + margin//2, y - miny + 35)
              for x, y in hex_corners(col_b, row_b)]
    shared = []
    for p1 in ca_pts:
        for p2 in cb_pts:
            if abs(p1[0]-p2[0]) < 2 and abs(p1[1]-p2[1]) < 2:
                shared.append(p1)
    if len(shared) >= 2:
        draw.line([shared[0], shared[1]], fill=color, width=width)

# Draw rivers
for fs in river_sides:
    draw_side_edge(fs, None, (255, 0, 255), 4)

# Draw roads  
for fs in road_sides:
    draw_side_edge(fs, None, (255, 100, 0), 4)

# Hex IDs for reference (small, top-left of each hex)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
except:
    font = ImageFont.load_default()

for col in range(1, NC+1):
    for row in range(1, NR+1):
        cx, cy = hex_centre(col, row)
        cx = cx - minx + margin // 2
        cy = cy - miny + 35
        hid = f'{col:02d}{row:02d}'
        # Only draw every other hex ID to avoid clutter
        if col <= 5 or row <= 5 or col >= 16 or row >= 19:
            draw.text((cx + 10, cy - 6), hid, fill=(80, 80, 80), font=font)

# Place labels
for hid, pl in feats['places'].items():
    col, row = parse_hex(hid)
    cx, cy = hex_centre(col, row)
    cx = cx - minx + margin // 2
    cy = cy - miny + 35
    draw.text((cx - 30, cy + 8), pl['name'][:12], fill=(0, 0, 100), font=font)

# Title
try:
    font_big = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
except:
    font_big = font
draw.text((10, 5), "Model Rivers (magenta) & Roads (orange) on Hex Grid",
          fill=(0, 0, 0), font=font_big)
draw.text((10, 25), f"River sides: {len(feats['river_sides'])}  "
          f"Road sides: {len(feats['road_sides'])}  "
          f"Road hexes: {len(feats['road_hexes'])}",
          fill=(0, 0, 0), font=font)

out = os.path.join(ROOT, 'model_rr_hexgrid.jpg')
canvas.save(out, quality=92)
print(f'Saved: {out}')
print(f'River sides: {len(feats["river_sides"])}')
print(f'Road sides: {len(feats["road_sides"])}')

# List rivers/roads per hex for inspection
print('\n=== RIVER SIDES (model) ===')
for r in feats['river_sides'][:30]:
    print(f'  {r[0]} | {r[1]}')
print(f'  ... and {len(feats["river_sides"])-30} more')

print('\n=== ROAD SIDES (model) ===')
for r in feats['road_sides'][:30]:
    print(f'  {r[0]} | {r[1]}')
print(f'  ... and {len(feats["road_sides"])-30} more')
