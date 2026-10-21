"""The original board artwork as a single 20x23 image.

The board was photographed in two halves (map1.jpg = rows 01-12,
map2.jpg = rows 13-23).  ``geometry.BOARD_Y_OFF`` maps map2 into map1's
pixel frame, so pasting the two scans at those offsets produces one
continuous board image that the map canvas can use as a "real map"
underlay instead of the flat terrain fills.

The stitched image is cached in _refs/board_scan.jpg (downscaled, since
the raw scans are 3510x4266 px).  ``scan_rect()`` returns the rectangle
that image actually covers in unified board pixel coordinates - the raw
scans include a white paper margin, so the rect is trimmed to the
artwork rather than to the canvas, otherwise the map canvas would paint
a white band over the bottom hex row.
"""
import os

from PIL import Image

from geometry import SCANS, BOARD_Y_OFF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, '_refs')
SCAN_PATH = os.path.join(REFS, 'board_scan.jpg')
MAX_WIDTH = 1800
WHITE = 248          # a pixel this bright counts as paper, not artwork


def _raw_size():
    """(width, height) of the stitched board in unified scan pixels."""
    w = 0
    h = 0
    for name, p in SCANS.items():
        path = os.path.join(REFS, name)
        if not os.path.exists(path):
            return None
        iw, ih = Image.open(path).size
        w = max(w, iw)
        h = max(h, ih + BOARD_Y_OFF[name])
    return (w, int(h) + 20)


def _stitched_full():
    """The two scans pasted into one canvas, at full resolution."""
    size = _raw_size()
    if size is None:
        return None
    w, h = size
    board = Image.new('RGB', (w, h), (255, 255, 255))
    for name, p in SCANS.items():
        img = Image.open(os.path.join(REFS, name)).convert('RGB')
        board.paste(img, (0, int(round(BOARD_Y_OFF[name]))))
    return board


_RECT = None


def scan_rect():
    """(x, y, w, h) of the artwork in unified board pixel coordinates.

    Trimming to the non-white content keeps the rect and the cached image
    describing exactly the same pixels, so stretching the downscaled
    cache to this rect never smears or leaves a white band.
    """
    global _RECT
    if _RECT is not None:
        return _RECT
    board = _stitched_full()
    if board is None:
        return None
    w, h = board.size
    step = 3

    def col_full(x):
        for y in range(0, h, step):
            p = board.getpixel((x, y))
            if p[0] < WHITE or p[1] < WHITE or p[2] < WHITE:
                return True
        return False

    def row_full(y):
        for x in range(0, w, step):
            p = board.getpixel((x, y))
            if p[0] < WHITE or p[1] < WHITE or p[2] < WHITE:
                return True
        return False

    left = next((x for x in range(w) if col_full(x)), 0)
    right = next((x for x in range(w - 1, -1, -1) if col_full(x)), w - 1)
    top = next((y for y in range(h) if row_full(y)), 0)
    bottom = next((y for y in range(h - 1, -1, -1) if row_full(y)), h - 1)
    _RECT = [left, top, right + 1, bottom + 1]
    return _RECT


def stitch(width=None):
    """Return the stitched board artwork as a PIL image (RGB).

    ``width`` downscales the result; the aspect ratio is preserved.
    """
    rect = scan_rect()
    if rect is None:
        return None
    board = _stitched_full().crop(tuple(rect))
    w, h = board.size
    if width and width < w:
        resample = getattr(Image, 'Resampling', Image).LANCZOS
        board = board.resize((width, int(round(h * width / w))), resample)
    return board


def scan_image(path=SCAN_PATH, width=MAX_WIDTH):
    """Build (or reuse) the cached stitched scan and return its path."""
    if not os.path.exists(path):
        img = stitch(width)
        if img is None:
            return None
        img.save(path, quality=86)
    return path


if __name__ == '__main__':
    from geometry import board_bounds
    p = scan_image()
    rect = scan_rect()
    print('wrote', p)
    print('scan rect :', rect)
    print('board bounds:', [round(v, 1) for v in board_bounds()])
    print('size:', Image.open(p).size)

