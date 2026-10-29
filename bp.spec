# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for a single self-contained BarbarianPrince.exe.

    pyinstaller --noconfirm --clean bp.spec

The game only needs data/ (the model) and web/ (the browser front end) at run
time, plus the rectified board scan for the "original artwork" view.  scipy is
excluded: it is only used to re-trace rivers and roads from the scan, which the
shipped game never does - it loads data/features.json.
"""
import os

ROOT = os.path.abspath(os.getcwd())

datas = [
    (os.path.join(ROOT, 'data', '*.json'), 'data'),
    (os.path.join(ROOT, 'data', 'board_preview.png'), 'data'),
    (os.path.join(ROOT, 'web'), 'web'),
    (os.path.join(ROOT, '_refs', 'BPMap_rectified.jpg'), '_refs'),
]

hiddenimports = [
    # main.py imports these lazily, so PyInstaller cannot see them
    'web', 'gui', 'cli', 'autoplay', 'camp_dp',
    # uvicorn picks its loop/protocol implementation at run time
    'uvicorn', 'uvicorn.logging',
    'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.loops.asyncio',
    'uvicorn.protocols', 'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto', 'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off',
]

a = Analysis(
    [os.path.join(ROOT, 'src', 'main.py')],
    pathex=[os.path.join(ROOT, 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['scipy', 'pandas', 'matplotlib', 'pytest', 'PyInstaller',
              'numpy.f2py', 'tkinter.test', 'test'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BarbarianPrince',
    debug=False,
    strip=False,
    upx=False,
    console=False,          # a double-click opens the Tk window, no console
    icon=None,
)
