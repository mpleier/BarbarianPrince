# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: BarbarianPrince as a portable folder (no temp extraction).

    python build_exe.py            # dist/BarbarianPrince/
    python build_exe.py --onefile  # dist/BarbarianPrince.exe (unpacks to %TEMP%)

The folder build starts instantly and never writes to a temporary directory:
the exe loads its DLLs and data from `_internal/` next to itself.  The single
file build is kept for convenience, but it unpacks a copy to `%TEMP%` on every
run.

The game only needs data/ (the model) and web/ (the browser front end) at run
time, plus the rectified board scan for the "original artwork" view.  scipy is
excluded: it is only used to re-trace rivers and roads from the scan, which the
shipped game never does - it loads data/features.json.
"""
import os

ROOT = os.path.abspath(os.getcwd())
ONEFILE = os.environ.get('BP_ONEFILE') == '1'

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
    # PIL's Tk bridge draws the board scan without writing a temp file
    'PIL.ImageTk',
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

if ONEFILE:
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
        console=False,
        icon=None,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='BarbarianPrince',
        debug=False,
        strip=False,
        upx=False,
        console=False,
        icon=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name='BarbarianPrince',
    )
