"""Fetch PyInstaller into ._vendor without pip.

pip cannot install on this machine (its unpack step is killed by the file
sandbox / OneDrive locking), so the wheels are downloaded straight from PyPI
and unzipped by hand.  Run once, then:

    $env:PYTHONPATH = "$PWD\\._vendor"
    python build_exe.py
"""
import json
import os
import sys
import urllib.request
import zipfile

VENDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '._vendor')
WHEELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '._wheels')

PACKAGES = ['pyinstaller', 'pyinstaller-hooks-contrib', 'altgraph',
            'pefile', 'pywin32-ctypes']


def pick(pkg):
    with urllib.request.urlopen(f'https://pypi.org/pypi/{pkg}/json',
                                timeout=60) as r:
        data = json.load(r)
    version = data['info']['version']
    files = data['releases'][version]
    for f in files:
        name = f['filename']
        if not name.endswith('.whl'):
            continue
        if 'win_amd64' in name or 'none-any' in name or 'py2.py3-none-any' in name:
            if 'macosx' in name or 'manylinux' in name or 'win32.whl' in name:
                continue
            return name, f['url'], version
    raise SystemExit(f'no usable wheel for {pkg}')


def main():
    os.makedirs(VENDOR, exist_ok=True)
    os.makedirs(WHEELS, exist_ok=True)
    for pkg in PACKAGES:
        name, url, version = pick(pkg)
        target = os.path.join(WHEELS, name)
        if not os.path.exists(target):
            print(f'download {name}')
            with urllib.request.urlopen(url, timeout=120) as r, open(target, 'wb') as f:
                f.write(r.read())
        print(f'unpack   {name}')
        with zipfile.ZipFile(target) as z:
            z.extractall(VENDOR)
        print(f'         {pkg} {version}')
    print(f'\nvendored into {VENDOR}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
