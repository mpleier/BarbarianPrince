"""Visual comparison: hex grid with model rivers/roads scaled to match original map."""
import json, os, math
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'data')

with open(os.path.join(DATA, 'features.json'), encoding='utf-8') as f:
    feats = json.load(f)

NC, NR = 20, 23
R = 50.0
SQ3 = math.sqrt(3.0)
DX = 1.5 * R
DY = SQ3 * R

def parse(hid):
    return int(hid[:2]), int(hid[2:])

def centre(col, row):
    i = col - 1
    return (DX * i, DY * (row - 1) + (i % 2) * DY / 2.0)

def corners(col, row):
    cx, cy = centre(col, row)
    return [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
            for a in range(0, 360, 60)]

# Board bounds
all_c = []
for col in range(1, NC + 1):
    for row in range(1, NR + 1):
        all_c.extend(corners(col, row))
minx = min(c[0] for c in all_c)
miny = min(c[1] for c in all_c)
w = max(c[0] for c in all_c) - minx
h = max(c[1] for c in all_c) - miny

# Open original map and resize to model hex grid
img = Image.open(os.path.join(ROOT, 'barbarianprince_onepiecemap-revc.jpg')).convert('RGB')
iw, ih = img.size

# The original map has a sidebar on the left (map key), need to crop it out
# Estimate sidebar width (~5% of image)
sidebar = int(iw * 0.06)
map_img = img.crop((sidebar, 0, iw, ih))
mw, mh = map_img.size

# Draw hex grid with rivers and roads
W = int(w) + 60
H = int(h) + 40
canvas = Image.new('RGB', (W, H), (245, 245, 240))
draw = ImageDraw.Draw(canvas)

try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 10)
    font_b = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
except:
    font = ImageFont.load_default()
    font_b = font

margin_x = 30
margin_y = 25

# Draw hex outlines
for col in range(1, NC + 1):
    for row in range(1, NR + 1):
        pts = [(x - minx + margin_x, y - miny + margin_y) for x, y in corners(col, row)]
        draw.polygon(pts, fill=(215, 228, 200), outline=(170, 170, 150), width=1)
        # Hex IDs in every 5th hex for reference
        if col % 5 == 1 or row % 5 == 1:
            cx, cy = (centre(col, row)[0] - minx + margin_x,
                     centre(col, row)[1] - miny + margin_y)
            draw.text((cx + 8, cy - 5), f'{col:02d}{row:02d}', fill=(120, 120, 100), font=font)

# Shared edge between two adjacent hexes
def shared_edge(a, b):
    col_a, row_a = parse(a)
    col_b, row_b = parse(b)
    ca = [(x - minx + margin_x, y - miny + margin_y) for x, y in corners(col_a, row_a)]
    cb = [(x - minx + margin_x, y - miny + margin_y) for x, y in corners(col_b, row_b)]
    shared = []
    for p1 in ca:
        for p2 in cb:
            if abs(p1[0] - p2[0]) < 2 and abs(p1[1] - p2[1]) < 2:
                shared.append(p1)
    return shared

# Draw model rivers (magenta, thick)
for a, b in feats['river_sides']:
    pts = shared_edge(a, b)
    if len(pts) >= 2:
        draw.line([pts[0], pts[1]], fill=(200, 0, 200), width=3)

# Draw model roads (orange, thick)
for a, b in feats['road_sides']:
    pts = shared_edge(a, b)
    if len(pts) >= 2:
        draw.line([pts[0], pts[1]], fill=(240, 140, 0), width=3)

# Highlight Huldra Castle area
cx1212, cy1212 = centre(12, 12)
cx1212 -= minx + margin_x
cy1212 -= miny + margin_y
# Actually add margin
cx1212 += margin_x
cy1212 += margin_y
draw.ellipse([cx1212 - 15, cy1212 - 15, cx1212 + 15, cy1212 + 15],
            outline=(255, 0, 0), width=3)
draw.text((cx1212 - 30, cy1212 + 15), "Huldra", fill=(255, 0, 0), font=font)

# Draw Nesser River label position
cx511, cy511 = centre(5, 11)
cx511 += margin_x - minx
cy511 += margin_y - miny
draw.text((cx511 + 10, cy511 - 5), "Nesser", fill=(0, 0, 200), font=font)

# Title
draw.text((10, 5), "Model Rivers (magenta) / Roads (orange) — compare with map below", fill=(0, 0, 0), font=font_b)
draw.text((10, 22), f"River sides: {len(feats['river_sides'])}  Road sides: {len(feats['road_sides'])}", fill=(80, 80, 80), font=font)

# Composite: left=model, right=original map, scaled to match
canvas_resized = canvas.resize((mw, mh), Image.LANCZOS)

side_by_side = Image.new('RGB', (mw * 2 + 200, mh + 50), (200, 200, 195))
draw2 = ImageDraw.Draw(side_by_side)
draw2.text((10, 5), "MODEL (left) vs ORIGINAL MAP (right)", fill=(0, 0, 0), font=font_b)
side_by_side.paste(canvas_resized, (100, 30))
side_by_side.paste(map_img, (mw + 200, 30))

out = os.path.join(ROOT, 'side_by_side_compare.jpg')
side_by_side.save(out, quality=90)
print(f'Saved: {out}')
print(f'Model grid: {W}x{H}, Map cropped: {mw}x{mh}')
