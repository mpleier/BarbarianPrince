"""The original board artwork as a single 20x23 image.

A scan of the full board is stored in `_refs/BPMap.jpg`
and served at `/scan/board.jpg`.  ``scan_rect()`` returns the rectangle
that image actually covers in pixel coordinates - the scan
includes a white paper margin, so the rect is trimmed to the
artwork rather than to the canvas, otherwise the map canvas would paint
a white band over the bottom hex row.

The hex-grid geometry (R=79.5, x0, y0, etc.) is stored in `geometry.py`
and was calibrated specifically for this one-piece scan.
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, '_refs')
SCAN_SOURCE = os.path.join(REFS, 'BPMap.jpg')
SCAN_PATH = os.path.join(REFS, 'board_scan.jpg')
MAX_WIDTH = 1800
WHITE = 248          # a pixel this bright counts as paper, not artwork


_RECT = None


def scan_rect():
    """(x, y, w, h) of the artwork in board pixel coordinates.

    Trimming to the non-white content keeps the rect and the cached image
    describing exactly the same pixels, so stretching the downscaled
    cache to this rect never smears or leaves a white band.
    """
    global _RECT
    if _RECT is not None:
        return _RECT
    if not os.path.exists(SCAN_SOURCE):
        return None
    im = Image.open(SCAN_SOURCE).convert('RGB')
    w, h = im.size
    A = im.load()
    step = 3

    def col_full(x):
        for y in range(0, h, step):
            p = A[x, y]
            if p[0] < WHITE or p[1] < WHITE or p[2] < WHITE:
                return True
        return False

    def row_full(y):
        for x in range(0, w, step):
            p = A[x, y]
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
    """Return the board artwork as a PIL image (RGB).

    ``width`` downscales the result; the aspect ratio is preserved.
    """
    if not os.path.exists(SCAN_SOURCE):
        return None
    rect = scan_rect()
    if rect is None:
        return None
    img = Image.open(SCAN_SOURCE).convert('RGB')
    board = img.crop(tuple(rect))
    w, h = board.size
    if width and width < w:
        resample = getattr(Image, 'Resampling', Image).LANCZOS
        board = board.resize((width, int(round(h * width / w))), resample)
    return board


def scan_image(path=SCAN_PATH, width=MAX_WIDTH):
    """Build (or reuse) the cached board scan and return its path."""
    if not os.path.exists(path):
        img = stitch(width)
        if img is None:
            return None
        img.save(path, quality=86)
    return path


def original_scan_path():
    """Return the path to the original full-resolution scan image.
    
    Use this when serving the scan to the web frontend so that the
    image pixel coordinates match the geometry-calibrated hex centers
    exactly, without any scaling mismatch.
    """
    return SCAN_SOURCE


if __name__ == '__main__':
    from geometry import board_bounds
    p = scan_image()
    rect = scan_rect()
    print('wrote', p)
    print('scan rect :', rect)
    print('board bounds:', [round(v, 1) for v in board_bounds()])
    print('size:', Image.open(p).size)

