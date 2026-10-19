#!/usr/bin/env python3
"""Portable, optimistic Testmon memory for the fast development loop."""
import argparse
import json
import logging
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

from scripts.smart_testing_inputs import changed_consumers, load_state, save_state

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'tests/smart-testing'
CACHE = ROOT / '.smart-testing'
MARKERS = 'not integration and not slow and not adherence'
LOG = logging.getLogger(__name__)


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


def run_tests(paths, database, inputs, selection):
    env = dict(os.environ, TESTMON_DATAFILE=str(database),
               SMART_TESTING_INPUTS=str(inputs))
    complete = '--no-testmon' in selection or '--testmon-noselect' in selection
    env['SMART_TESTING_COMPLETE'] = ('all' if paths == ['tests/'] else 'modules') if complete else ''
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    command = [sys.executable, '-m', 'pytest', *paths, '-m', MARKERS,
               '-p', 'scripts.smart_testing_inputs', *selection]
    return subprocess.run(command, env=env, check=False).returncode


def prepare(database, inputs):
    """A local DB owns its own baseline; reference-only changes never replace it."""
    if database.exists() and inputs.exists():
        return
    partial = database.exists() or inputs.exists()
    if partial:
        LOG.info('Incomplete private state; learning the fast tier once.')
        database.unlink(missing_ok=True)
        inputs.unlink(missing_ok=True)
    metadata = REFERENCE / 'reference.json'
    dump = REFERENCE / 'reference.sql'
    if not partial and metadata.exists() and dump.exists():
        reference = json.loads(metadata.read_text())
        if reference.get('schema') == 2 and reference.get('scope') == MARKERS:
            restore(dump, database)
            save_state(inputs, {'inputs': reference['inputs'], 'stats': {}})
            LOG.info('Restored reference; Testmon will check environment compatibility.')
            return
    LOG.info('No compatible reference; learning the fast tier once.')
    save_state(inputs, {'inputs': {}, 'stats': {}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true',
                        help='run the fast tier and export portable state')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='smart-test: %(message)s')
    os.chdir(ROOT)
    database = CACHE / 'testmon.db'
    inputs = CACHE / 'inputs.json'
    prepare(database, inputs)
    if not args.refresh:
        state = load_state(inputs)
        changed = changed_consumers(ROOT, state)
        save_state(inputs, state)  # Retain stat/hash memoization, not learned baselines.
        if changed:
            paths = ['tests/'] if '*' in changed else sorted(changed)
            LOG.info('Changed recorded file inputs: checking %s', ', '.join(paths))
            status = run_tests(paths, database, inputs, ['--no-testmon'])
            if status == 5:
                # Consumers can move out of the fast tier or lose their tests.
                state = load_state(inputs)
                for consumer in changed:
                    state['inputs'].pop(consumer, None)
                save_state(inputs, state)
            elif status:
                return status
    selection = ['--testmon', '--testmon-noselect' if args.refresh else '--testmon-forceselect']
    status = run_tests(['tests/'], database, inputs, selection)
    # All native-selected tests can be excluded by the fast-tier marker.
    if status == 5 and not args.refresh:
        return 0
    if status:
        return status
    if args.refresh:
        REFERENCE.mkdir(exist_ok=True)
        with sqlite3.connect(database) as connection:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            dump = f'PRAGMA user_version={version};\n' + '\n'.join(connection.iterdump()) + '\n'
        state = load_state(inputs)
        # These are transport artifacts; local learned state remains authoritative.
        save_state(REFERENCE / 'reference.json', {
            'schema': 2, 'scope': MARKERS, 'inputs': state['inputs'],
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
        })
        fd, temporary = tempfile.mkstemp(dir=REFERENCE)
        try:
            with os.fdopen(fd, 'w') as stream:
                stream.write(dump)
            os.replace(temporary, REFERENCE / 'reference.sql')
        finally:
            Path(temporary).unlink(missing_ok=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
