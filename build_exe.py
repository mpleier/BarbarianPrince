"""Build the portable Barbarian Prince app for Windows.

    python build_exe.py             # dist/BarbarianPrince/  (folder, no temp dir)
    python build_exe.py --onefile   # dist/BarbarianPrince.exe (unpacks to %TEMP%)

Requires PyInstaller (``pip install pyinstaller``).  The folder build is the
default: the exe runs straight from `dist/BarbarianPrince/` and never creates a
temporary directory, so it starts instantly and leaves nothing behind.  Copy
the whole folder wherever you like and double-click the exe.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(ROOT, 'dist', 'BarbarianPrince')
EXE_IN_FOLDER = os.path.join(FOLDER, 'BarbarianPrince.exe')
ONEFILE = os.path.join(ROOT, 'dist', 'BarbarianPrince.exe')


def have_pyinstaller():
    if shutil.which('pyinstaller'):
        return True
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def folder_size(path):
    total = 0
    for base, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(base, name))
            except OSError:
                pass
    return total / (1024 * 1024)


def main(argv):
    onefile = '--onefile' in argv
    if not have_pyinstaller():
        print('PyInstaller is missing.  Install it with:')
        print('    python -m pip install pyinstaller')
        return 1

    env = dict(os.environ)
    env['BP_ONEFILE'] = '1' if onefile else '0'
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
           'bp.spec']
    print(' '.join(cmd), '(onefile)' if onefile else '(folder)')
    subprocess.check_call(cmd, cwd=ROOT, env=env)

    if onefile:
        if not os.path.exists(ONEFILE):
            print('build finished but', ONEFILE, 'is missing')
            return 1
        print(f'\nbuilt {ONEFILE} ({os.path.getsize(ONEFILE) / (1024 * 1024):.1f} MB)')
        print('  note: this variant unpacks itself into %TEMP% on every run')
        target = ONEFILE
    else:
        if not os.path.exists(EXE_IN_FOLDER):
            print('build finished but', EXE_IN_FOLDER, 'is missing')
            return 1
        print(f'\nbuilt {FOLDER} ({folder_size(FOLDER):.1f} MB total)')
        print('  runs in place - no temporary directory is created')
        target = EXE_IN_FOLDER

    print(f'\n  "{target}"                     play (Tk window)')
    print(f'  "{target}" --web               play in the browser')
    print(f'  "{target}" --auto --seed 7     bot campaign')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
