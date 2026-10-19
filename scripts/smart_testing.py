#!/usr/bin/env python3
"""Portable, opt-in Testmon memory for the fast development loop."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'tests/smart-testing'
CACHE = ROOT / '.smart-testing'
MARKERS = 'not integration and not slow and not adherence'


def environment():
    return {
        'python': list(sys.version_info[:3]),
        'packages': sorted((d.metadata['Name'].lower(), d.version)
                           for d in importlib.metadata.distributions()),
    }


def external_inputs(root):
    """Testmon cannot observe reads of shell, prose, configuration or data."""
    paths = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        cwd=root).decode().split('\0')
    digest = hashlib.sha256()
    for name in sorted(set(paths) - {''}):
        if name.endswith('.py') or name.startswith('tests/smart-testing/'):
            continue
        path = root / name
        digest.update(name.encode() + b'\0')
        digest.update(path.read_bytes() if path.is_file() else b'<missing>')
    return digest.hexdigest()


def restore(dump, database):
    """Restore only into a private, newly created database; publish atomically."""
    database.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=database.parent)
    os.close(fd)
    try:
        with sqlite3.connect(name) as connection:
            connection.executescript(dump.read_text())
            if connection.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                raise ValueError('Testmon reference failed integrity check')
        os.replace(name, database)
    finally:
        Path(name).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true',
                        help='explicitly run all fast tests and publish a reference')
    args = parser.parse_args()
    os.chdir(ROOT)
    metadata = REFERENCE / 'reference.json'
    dump = REFERENCE / 'reference.sql'
    database = CACHE / 'testmon.db'
    current = json.loads(json.dumps(environment()))
    if not args.refresh:
        if not metadata.exists() or not dump.exists():
            parser.error('No reference. Run make smart-refresh explicitly.')
        reference = json.loads(metadata.read_text())
        if reference['environment'] != current:
            parser.error('Environment differs from reference; use the locked environment or explicitly refresh.')
        if reference['external_inputs'] != external_inputs(ROOT):
            parser.error('Non-Python inputs changed; run make check-fast explicitly (Testmon cannot track these reads).')
        if not database.exists():
            restore(dump, database)
    else:
        CACHE.mkdir(exist_ok=True)
        database.unlink(missing_ok=True)
    env = dict(os.environ, TESTMON_DATAFILE=str(database))
    # Children invoking python3 receive the same environment as their parent.
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    command = [sys.executable, '-m', 'pytest', 'tests/', '-m', MARKERS,
               '--testmon', '--testmon-noselect' if args.refresh else '--testmon-forceselect']
    result = subprocess.run(command, env=env, check=False)
    # Pytest uses 5 when Testmon deselects every unchanged test.
    if result.returncode == 5 and not args.refresh:
        return 0
    if result.returncode:
        return result.returncode
    if args.refresh:
        REFERENCE.mkdir(exist_ok=True)
        with sqlite3.connect(database) as connection:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            dump.write_text(f'PRAGMA user_version={version};\n'
                            + '\n'.join(connection.iterdump()) + '\n')
        metadata.write_text(json.dumps({
            'environment': current,
            'external_inputs': external_inputs(ROOT),
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
            'scope': MARKERS,
        }, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
