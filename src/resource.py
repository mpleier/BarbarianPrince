"""Locate the bundled resources, whether run from source or frozen.

PyInstaller's one-file build unpacks into ``sys._MEIPASS``, so ``__file__``
points into a temporary directory.  Every module that needs ``data/``, ``web/``
or ``_refs/`` asks here instead of walking up from its own file.
"""
import os
import sys

FROZEN = bool(getattr(sys, 'frozen', False))

if FROZEN:
    ROOT = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA = os.path.join(ROOT, 'data')
WEB = os.path.join(ROOT, 'web')
REFS = os.path.join(ROOT, '_refs')
