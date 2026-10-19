"""Record repository file reads that execution coverage cannot observe.

Loaded only by smart_testing.py, in disposable pytest child processes.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

import pytest

EXCLUDED = {'.git', '.venv', '.smart-testing', '.pytest_cache', '.panel', '.tmp', '__pycache__'}
REFERENCE_FILES = {'tests/smart-testing/reference.json', 'tests/smart-testing/reference.sql'}


def load_state(path):
    if not path.exists():
        return {'inputs': {}, 'stats': {}}
    return json.loads(path.read_text())


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(state, stream, sort_keys=True)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def fingerprint(root, name, stats):
    """Hash known inputs only, reusing content hashes while stat identity holds."""
    path = root / name
    try:
        info = path.stat()
        stamp = [info.st_dev, info.st_ino, info.st_mode, info.st_size,
                 info.st_mtime_ns, info.st_ctime_ns]
        previous = stats.get(name)
        if previous and previous[0] == stamp:
            return previous[1]
        if path.is_file():
            digest = hashlib.sha256(str(info.st_mode & 0o7777).encode() + b'\0'
                                    + path.read_bytes()).hexdigest()
        else:
            digest = 'not-a-file'
    except FileNotFoundError:
        stamp, digest = None, 'missing'
    stats[name] = [stamp, digest]
    return digest


def changed_consumers(root, state):
    current = {}
    changed = set()
    for consumer, inputs in list(state['inputs'].items()):
        if consumer != '*' and not (root / consumer).is_file():
            del state['inputs'][consumer]
            continue
        for name, learned in inputs.items():
            if name not in current:
                current[name] = fingerprint(root, name, state['stats'])
            if current[name] != learned:
                changed.add(consumer)
    return changed


class FileReads:
    def __init__(self, root, path):
        self.root = root
        self.path = path
        self.state = load_state(path)
        self.consumer = None
        self.observed = {}
        self.busy = False
        self.executed = set()

    def audit(self, event, args):
        if event != 'open' or self.consumer is None or self.busy:
            return
        name, mode, flags = args
        if not isinstance(name, (str, bytes)) or flags & os.O_ACCMODE == os.O_WRONLY:
            return
        # Attribute explicit project reads, not pytest/importer's source loading.
        frame = sys._getframe(1)
        while frame:
            caller = (frame.f_globals.get('__file__') or frame.f_code.co_filename)
            if ('importlib._bootstrap' in caller or caller.endswith('/importlib/_bootstrap_external.py')
                    or '/_pytest/' in caller or '/testmon/' in caller):
                return
            if caller != __file__ and Path(caller).is_absolute():
                origin = Path(caller).resolve()
                if origin.is_relative_to(self.root) and not EXCLUDED.intersection(
                        origin.relative_to(self.root).parts):
                    break
            frame = frame.f_back
        else:
            return
        self.busy = True
        try:
            path = Path(os.fsdecode(name)).absolute()
            try:
                relative = path.relative_to(self.root)
            except ValueError:
                return
            if EXCLUDED.intersection(relative.parts) or relative.suffix == '.pyc':
                return
            key = relative.as_posix()
            if key in REFERENCE_FILES:
                return  # Exported cache state cannot fingerprint itself.
            digest = fingerprint(self.root, key, self.state['stats'])
            consumer = self.consumer
            # A module can initialize cached globals via a helper, including
            # on a lazy runtime import. Such reads can feed other test modules.
            while frame:
                filename = (frame.f_globals.get('__file__') or frame.f_code.co_filename)
                if frame.f_code.co_name == '<module>' and Path(filename).is_absolute():
                    owner = Path(filename).resolve()
                    if owner.is_relative_to(self.root) and not EXCLUDED.intersection(
                            owner.relative_to(self.root).parts):
                        if owner.relative_to(self.root).as_posix() != consumer:
                            consumer = '*'
                        break
                frame = frame.f_back
            self.observed.setdefault(consumer, {})[key] = digest
        finally:
            self.busy = False

    @pytest.hookimpl(hookwrapper=True)
    def pytest_make_collect_report(self, collector):
        previous = self.consumer
        path = collector.path
        self.consumer = path.relative_to(self.root).as_posix() if (
            path.suffix == '.py' and path.is_relative_to(self.root)) else None
        yield
        self.consumer = previous

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item):
        self.consumer = item.path.relative_to(self.root).as_posix()
        self.executed.add(self.consumer)
        yield
        self.consumer = None

    def pytest_sessionfinish(self, session, exitstatus):
        self.consumer = None
        if exitstatus != 0:
            return  # Failed consumers must remain stale and run again next time.
        complete = os.environ.get('SMART_TESTING_COMPLETE')
        if complete == 'all':
            self.state['inputs'] = {'*': self.observed.get('*', {})}
        if complete in {'all', 'modules'}:
            for consumer in self.executed:
                self.state['inputs'][consumer] = self.observed.get(consumer, {})
        for consumer, inputs in self.observed.items():
            if consumer == '*' or consumer in self.executed:
                self.state['inputs'].setdefault(consumer, {}).update(inputs)
        known = set().union(*(set(inputs) for inputs in self.state['inputs'].values()))
        self.state['stats'] = {name: stamp for name, stamp in self.state['stats'].items()
                               if name in known}
        save_state(self.path, self.state)


def pytest_configure(config):
    state_path = os.environ.get('SMART_TESTING_INPUTS')
    if state_path:
        recorder = FileReads(Path(config.rootpath).resolve(), Path(state_path))
        sys.addaudithook(recorder.audit)
        config.pluginmanager.register(recorder, 'smart-file-reads')
