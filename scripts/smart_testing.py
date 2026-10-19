#!/usr/bin/env python3
"""Portable, optimistic Testmon memory for the development loop."""
import argparse
import json
import logging
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

from scripts.smart_testing_inputs import SCOPE, changed_consumers, load_state, save_state

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'tests/smart-testing'
CACHE = ROOT / '.smart-testing'
MARKERS = 'not smart_always'
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


def run_tests(paths, database, inputs, selection, markers=MARKERS):
    env = dict(os.environ, TESTMON_DATAFILE=str(database),
               SMART_TESTING_INPUTS=str(inputs), SMART_TESTING_SCOPE=SCOPE)
    complete = markers != 'smart_always' and (
        '--no-testmon' in selection or '--testmon-noselect' in selection)
    env['SMART_TESTING_COMPLETE'] = ('all' if paths == ['tests/'] else 'modules') if complete else ''
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    command = [sys.executable, '-m', 'pytest', *paths,
               '-p', 'scripts.smart_testing_inputs', *selection]
    if markers:
        command.extend(['-m', markers])
    return subprocess.run(command, env=env, check=False).returncode


def prepare(database, inputs):
    """A local DB owns its own baseline; reference-only changes never replace it."""
    if database.exists() and inputs.exists():
        return load_state(inputs).get('scope') != SCOPE
    partial = database.exists() or inputs.exists()
    if partial:
        LOG.info('Incomplete private state; learning the selected suite once.')
        database.unlink(missing_ok=True)
        inputs.unlink(missing_ok=True)
    metadata = REFERENCE / 'reference.json'
    dump = REFERENCE / 'reference.sql'
    if not partial and metadata.exists() and dump.exists():
        reference = json.loads(metadata.read_text())
        if reference.get('schema') == 3 and reference.get('scope') == SCOPE:
            restore(dump, database)
            save_state(inputs, {'inputs': reference['inputs'], 'stats': {},
                                'always': reference.get('always', []), 'scope': SCOPE})
            LOG.info('Restored reference; Testmon will check environment compatibility.')
            return False
    LOG.info('No compatible reference; learning the selected suite once.')
    save_state(inputs, {'inputs': {}, 'stats': {}, 'always': []})
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true',
                        help='run every tier and export portable state')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='smart-test: %(message)s')
    os.chdir(ROOT)
    database = CACHE / 'testmon.db'
    inputs = CACHE / 'inputs.json'
    learn = prepare(database, inputs)
    if not args.refresh and not learn:
        state = load_state(inputs)
        changed = changed_consumers(ROOT, state)
        save_state(inputs, state)  # Retain stat/hash memoization, not learned baselines.
        if changed:
            paths = ['tests/'] if '*' in changed else sorted(changed)
            LOG.info('Changed recorded file inputs: checking %s', ', '.join(paths))
            status = run_tests(paths, database, inputs, ['--no-testmon'])
            if status == 5:
                # Consumer modules can lose their cacheable tests.
                state = load_state(inputs)
                for consumer in changed:
                    state['inputs'].pop(consumer, None)
                save_state(inputs, state)
            elif status:
                return status
    selection = ['--testmon', '--testmon-noselect' if args.refresh or learn else '--testmon-forceselect']
    status = run_tests(['tests/'], database, inputs, selection,
                       markers=None if args.refresh else MARKERS)
    if status == 5 and not args.refresh:
        status = 0
    if status:
        return status
    if not args.refresh:
        always = load_state(inputs).get('always', [])
        if always:
            LOG.info('Checking live-state consumers: %s', ', '.join(always))
            status = run_tests(always, database, inputs, ['--no-testmon'], markers='smart_always')
            if status not in (0, 5):
                return status
    if args.refresh:
        REFERENCE.mkdir(exist_ok=True)
        with sqlite3.connect(database) as connection:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            dump = f'PRAGMA user_version={version};\n' + '\n'.join(connection.iterdump()) + '\n'
        state = load_state(inputs)
        # These are transport artifacts; local learned state remains authoritative.
        save_state(REFERENCE / 'reference.json', {
            'schema': 3, 'scope': SCOPE, 'inputs': state['inputs'],
            'always': state.get('always', []),
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
