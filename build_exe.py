"""Build dist/BarbarianPrince.exe - one file, no console, no installer.

    python build_exe.py

Requires PyInstaller (``pip install pyinstaller``).  The result bundles the
engine, the Tk interface, the browser front end, the model data and the board
scan, so it can be copied to any Windows machine and run by double-clicking.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(ROOT, 'dist', 'BarbarianPrince.exe')


def have_pyinstaller():
    if shutil.which('pyinstaller'):
        return True
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    if not have_pyinstaller():
        print('PyInstaller is missing.  Install it with:')
        print('    python -m pip install pyinstaller')
        return 1
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
           'bp.spec']
    print(' '.join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)
    if not os.path.exists(EXE):
        print('build finished but', EXE, 'is missing')
        return 1
    size = os.path.getsize(EXE) / (1024 * 1024)
    print(f'\nbuilt {EXE} ({size:.1f} MB)')
    print('  double-click            play (Tk window)')
    print('  BarbarianPrince.exe --web        play in the browser')
    print('  BarbarianPrince.exe --auto --seed 7   bot campaign (writes nothing)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
