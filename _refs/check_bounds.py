import sys
sys.path.insert(0, 'src')
from geometry import SCAN_X0, R, board_bounds
print('Left vertex of col 1:', SCAN_X0 - R)
print('Right vertex of col 20:', board_bounds()[2])
print('SCAN_X0:', SCAN_X0)
print('R:', R)
print('board_bounds:', board_bounds())
