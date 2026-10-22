"""Quick check: one-piece source vs geometry vs cached scan."""
import sys, math
sys.path.insert(0, 'src')
from PIL import Image
from geometry import R, DX, DY, NC, NR, board_bounds
from map_scan import scan_rect

src = Image.open('_refs/barbarianprince_onepiecemap-revc.jpg').size
cache = Image.open('_refs/board_scan.jpg').size
rect = scan_rect()
bb = board_bounds()

print("=== Image sizes ===")
print(f"  One-piece source: {src[0]}x{src[1]}")
print(f"  Content rect: {rect}  -> {rect[2]-rect[0]}x{rect[3]-rect[1]}")
print(f"  Cached board_scan: {cache[0]}x{cache[1]}")
print()
print("=== Geometry (R=106, from original scans) ===")
print(f"  Hex grid: {NC} cols x {NR} rows = {NC*NR} hexes")
print(f"  DX (col step): {DX:.1f}  DY (row step): {DY:.1f}")
print(f"  Board bounds: x={bb[0]:.1f}..{bb[2]:.1f}  ({bb[2]-bb[0]:.1f} px wide)")
print(f"               y={bb[1]:.1f}..{bb[3]:.1f}  ({bb[3]-bb[1]:.1f} px tall)")
print()
print("=== Size comparison ===")
print(f"  Source aspect ratio:   {src[0]/src[1]:.4f}")
print(f"  Content aspect ratio:  {(rect[2]-rect[0])/(rect[3]-rect[1]):.4f}")
print(f"  Geometry aspect ratio: {(bb[2]-bb[0])/(bb[3]-bb[1]):.4f}")
print(f"  Expected 20x23 ratio:  {30.5/(math.sqrt(3)*NR):.4f}")
print()
print("=== Discrepancy ===")
print(f"  Content width  vs geometry width:  {rect[2]-rect[0]} vs {bb[2]-bb[0]:.0f}  diff={((rect[2]-rect[0])-(bb[2]-bb[0])):.0f} px")
print(f"  Content height vs geometry height: {rect[3]-rect[1]} vs {bb[3]-bb[1]:.0f}  diff={((rect[3]-rect[1])-(bb[3]-bb[1])):.0f} px")
