#!/usr/bin/env python3
"""Portable, optimistic Testmon memory for the development loop."""
import argparse
import importlib.util
import json
import logging
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

# Load the sibling plugin by file, without adding the harness repository to the
# workload's import path or competing with its own `scripts` package.
SPEC = importlib.util.spec_from_file_location(
    'idh_smart_testing_inputs', Path(__file__).with_name('smart_testing_inputs.py'))
PLUGIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLUGIN)
SCOPE = PLUGIN.SCOPE
changed_consumers = PLUGIN.changed_consumers
load_state = PLUGIN.load_state
save_state = PLUGIN.save_state
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
    root = inputs.parent.parent
    receipt = inputs.with_name('session.status')
    receipt.unlink(missing_ok=True)
    env = dict(os.environ, TESTMON_DATAFILE=str(database),
               SMART_TESTING_INPUTS=str(inputs), SMART_TESTING_SCOPE=SCOPE,
               SMART_TESTING_ROOT=str(root), SMART_TESTING_SESSION=str(receipt))
    complete = markers != 'smart_always' and (
        '--no-testmon' in selection or '--testmon-noselect' in selection)
    env['SMART_TESTING_COMPLETE'] = ('all' if not paths else 'modules') if complete else ''
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    # -c preserves Python's normal cwd import path, unlike executing a script
    # from another repository. No PYTHONPATH or sys.path surgery is needed.
    bootstrap = ('import runpy, sys; entry = sys.argv.pop(1); '
                 'runpy.run_path(entry, run_name="__main__")')
    command = [sys.executable, '-c', bootstrap, str(Path(__file__).resolve()),
               '--root', str(root), '--pytest', '--rootdir', str(root),
               '--confcutdir', str(root), *paths, *selection, '-m', markers or '']
    status = subprocess.run(command, cwd=root, env=env, check=False).returncode
    if status in (0, 5) and not receipt.exists():
        LOG.error('pytest did not complete a test session; use the normal project check')
        return 4
    return status


def prepare(database, inputs, reference):
    """A local DB owns its own baseline; reference-only changes never replace it."""
    if database.exists() and inputs.exists():
        return load_state(inputs).get('scope') != SCOPE
    partial = database.exists() or inputs.exists()
    if partial:
        LOG.info('Incomplete private state; learning the selected suite once.')
        database.unlink(missing_ok=True)
        inputs.unlink(missing_ok=True)
    metadata = reference / 'reference.json'
    dump = reference / 'reference.sql'
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
    parser.add_argument('--root', type=Path, default=Path.cwd(),
                        help='workload checkout (default: current directory)')
    parser.add_argument('--pytest', action='store_true', help=argparse.SUPPRESS)
    args, pytest_args = parser.parse_known_args()
    if args.pytest:
        import pytest
        return pytest.main(pytest_args, plugins=[PLUGIN])
    if pytest_args:
        parser.error('unrecognized arguments: ' + ' '.join(pytest_args))
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f'workload root is not a directory: {root}')
    reference = root / 'tests/smart-testing'
    cache = root / '.smart-testing'
    logging.basicConfig(level=logging.INFO, format='smart-test: %(message)s')
    os.chdir(root)
    database = cache / 'testmon.db'
    inputs = cache / 'inputs.json'
    learn = prepare(database, inputs, reference)
    if not args.refresh and not learn:
        state = load_state(inputs)
        changed = changed_consumers(root, state)
        save_state(inputs, state)  # Retain stat/hash memoization, not learned baselines.
        if changed:
            paths = [] if '*' in changed else sorted(changed)
            LOG.info('Changed recorded file inputs: checking %s',
                     ', '.join(paths) if paths else 'the project suite')
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
    status = run_tests([], database, inputs, selection,
                       markers=None if args.refresh or learn else MARKERS)
    if status == 5 and not args.refresh and not learn:
        status = 0
    if status:
        return status
    if not args.refresh and not learn:
        always = load_state(inputs).get('always', [])
        if always:
            LOG.info('Checking live-state consumers: %s', ', '.join(always))
            status = run_tests(always, database, inputs, ['--no-testmon'], markers='smart_always')
            if status not in (0, 5):
                return status
    if args.refresh:
        reference.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(database) as connection:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            dump = f'PRAGMA user_version={version};\n' + '\n'.join(connection.iterdump()) + '\n'
        state = load_state(inputs)
        # These are transport artifacts; local learned state remains authoritative.
        save_state(reference / 'reference.json', {
            'schema': 3, 'scope': SCOPE, 'inputs': state['inputs'],
            'always': state.get('always', []),
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
        })
        fd, temporary = tempfile.mkstemp(dir=reference)
        try:
            with os.fdopen(fd, 'w') as stream:
                stream.write(dump)
            os.replace(temporary, reference / 'reference.sql')
        finally:
            Path(temporary).unlink(missing_ok=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
