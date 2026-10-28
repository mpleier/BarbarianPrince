"""Re-runnable quality check for BarbarianPrince.

Reproduces the _qc.txt format:
    ===== QC <timestamp> =====
    Python <version>
    compile-checked <N> files
    ERROR <path>
      <message>
    compile errors: <E>

    <unittest discover -v output>

    unittest exit: <code>
    DONE (bad=<E>, exit=<code>)

Usage:  python _qc_run.py
"""
import datetime
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {'.git', '__pycache__', '_refs/.venv', 'node_modules'}


def classify(rel):
    """Production modules must compile standalone; the engine fragments and
    the _refs scratchpad are expected not to be importable modules."""
    norm = rel.replace('\\', '/')
    if norm.startswith('src/_parts/'):
        return 'fragment'
    if norm.startswith('_refs/'):
        return 'scratch'
    return 'production'


def py_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith('.py'):
                p = os.path.join(dirpath, fn)
                if os.path.abspath(p) == os.path.abspath(__file__):
                    continue          # skip this runner
                out.append(p)
    return sorted(out)


def compile_check():
    errors = []
    checked = 0
    for p in py_files():
        rel = os.path.relpath(p, ROOT)
        try:
            with open(p, encoding='utf-8', errors='replace') as fh:
                src = fh.read()
            compile(src, rel, 'exec')
        except Exception as exc:                    # noqa: BLE001 - report all
            errors.append((rel, f'{type(exc).__name__}: {exc}', classify(rel)))
        else:
            checked += 1
    return checked, errors


def main():
    lines = []
    stamp = datetime.datetime.now().isoformat(timespec='seconds')
    lines.append(f'===== QC {stamp} =====')
    lines.append(sys.version.split()[0])

    checked, errors = compile_check()
    lines.append(f'compile-checked {checked + len(errors)} files')
    production = [e for e in errors if e[2] == 'production']
    artifacts = [e for e in errors if e[2] in ('fragment', 'scratch')]
    if production:
        for rel, msg, cat in production:
            lines.append(f'ERROR ({cat}) {rel}')
            lines.append(f'  {msg}')
    if artifacts:
        for rel, msg, cat in artifacts:
            lines.append(f'note ({cat}) {rel}')
            lines.append(f'  {msg}')
    lines.append(f'compile errors (production): {len(production)}')
    lines.append(f'non-module artifacts (fragments/scratch): {len(artifacts)}')
    lines.append('')

    # unit tests
    proc = subprocess.run(
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=600,
    )
    out = proc.stdout.rstrip()
    lines.append(out)
    if proc.stderr:
        lines.append(proc.stderr.rstrip())
    lines.append('')
    lines.append(f'unittest exit: {proc.returncode}')
    lines.append(f'DONE (bad={len(production)}, exit={proc.returncode})')

    report = os.path.join(ROOT, '_qc.txt')
    with open(report, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')

    print('\n'.join(lines))
    print(f'\n[qc] report written to {report}')
    return 0 if (not production and proc.returncode == 0) else 1


if __name__ == '__main__':
    sys.exit(main())
