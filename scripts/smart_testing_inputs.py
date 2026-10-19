"""Record repository file reads that execution coverage cannot observe.

Loaded by smart_testing.py; recording runs in disposable pytest children.
"""
import fnmatch
from functools import cache
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pytest

SCOPE = 'all-tiers-v5'

EXCLUDED = {'.git', '.venv', '.smart-testing', '.pytest_cache', '.panel', '.tmp', '__pycache__'}
REFERENCE_FILES = {'tests/smart-testing/reference.json', 'tests/smart-testing/reference.sql'}
MONITOR_FILES = {Path(__file__).resolve(), Path(__file__).with_name('smart_testing.py').resolve()}


def invocation_fingerprint():
    """Fingerprint pytest invocation policy without exporting raw option values."""
    values = {name: os.environ.get(name, '') for name in (
        'PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD')}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


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


@cache
def tracked_paths(root):
    return [os.fsdecode(name) for name in subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        cwd=root).split(b'\0') if name]


def glob_members(root, pattern):
    patterns = {pattern, pattern.replace('/**/', '/')}
    if pattern.startswith('**/'):
        patterns.add(pattern[3:])
    return sorted({name for name in tracked_paths(root)
                   if not EXCLUDED.intersection(Path(name).parts)
                   and name not in REFERENCE_FILES
                   and any(fnmatch.fnmatchcase(name, item) for item in patterns)})


@cache
def version_fingerprint(name):
    """One full version response per invocation; failed probes stay stale.

    An optional $NAME resolves an executable override from the environment.
    Store only hashes, never the response or environment value.
    """
    if name.startswith('$') and name[1:] not in os.environ:
        return 'unset'
    command = os.environ[name[1:]] if name.startswith('$') else name
    if not command:
        return 'unavailable:' + os.urandom(16).hex()
    try:
        result = subprocess.run(
            [command, '--version'], capture_output=True, timeout=10,
            env={key: value for key, value in os.environ.items() if key != 'BASH_ENV'},
        )
        if result.returncode == 0 and (result.stdout.strip() or result.stderr.strip()):
            return hashlib.sha256(json.dumps([
                result.stdout.hex(), result.stderr.hex(),
            ]).encode()).hexdigest()
    except FileNotFoundError:
        # An existing launcher can fail because its interpreter is missing.
        # Only a command absent from executable lookup is stable absence.
        if shutil.which(command) is None:
            return 'missing'
    except (OSError, subprocess.TimeoutExpired):
        pass
    return 'unavailable:' + os.urandom(16).hex()


def fingerprint(root, name, stats):
    """Hash known inputs only, reusing content hashes while stat identity holds."""
    if name.startswith('version:'):
        return version_fingerprint(name[len('version:'):])
    if name.startswith('glob:'):
        digest = hashlib.sha256()
        for member in glob_members(root, name[5:]):
            digest.update(member.encode() + b'\0' + fingerprint(root, member, stats).encode())
        return digest.hexdigest()
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
    except (FileNotFoundError, NotADirectoryError):
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
        self.invocation = os.environ.get('SMART_TESTING_ENVIRONMENT')
        self.consumer = None
        self.observed = {}
        self.busy = False
        self.executed = set()
        self.collected = set()
        self.always = set()
        for name in ('conftest.py', 'pytest.ini', '.pytest.ini', 'pytest.toml',
                     '.pytest.toml', 'pyproject.toml', 'setup.cfg', 'tox.ini',
                     'glob:**/conftest.py'):
            self.observed.setdefault('*', {})[name] = fingerprint(root, name, self.state['stats'])

    def audit(self, event, args):
        if event == 'subprocess.Popen' and self.consumer and not self.busy:
            self.record_command(args[1], args[2], args[3])
            return
        if event != 'open' or self.consumer is None or self.busy:
            return
        name, mode, flags = args
        if not isinstance(name, (str, bytes)) or flags & os.O_ACCMODE == os.O_WRONLY:
            return
        # Attribute explicit project reads, not pytest/importer's source loading.
        frame = sys._getframe(1)
        while frame:
            caller = (frame.f_globals.get('__file__') or frame.f_code.co_filename)
            module = frame.f_globals.get('__name__', '')
            if ('importlib._bootstrap' in caller or caller.endswith('/importlib/_bootstrap_external.py')
                    or module in ('_pytest', 'testmon')
                    or module.startswith(('_pytest.', 'testmon.'))):
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
                    if owner not in MONITOR_FILES and owner.is_relative_to(self.root) and not EXCLUDED.intersection(
                            owner.relative_to(self.root).parts):
                        if owner.relative_to(self.root).as_posix() != consumer:
                            consumer = '*'
                        break
                frame = frame.f_back
            self.observed.setdefault(consumer, {})[key] = digest
        finally:
            self.busy = False

    def record_command(self, command, cwd, environment):
        if not isinstance(command, (list, tuple)):
            return  # Shell-string indirect inputs use explicit declarations.
        command = [os.fsdecode(arg) if isinstance(arg, (str, bytes, os.PathLike)) else None
                   for arg in command]
        directory = Path(os.fsdecode(cwd)).absolute() if cwd else Path.cwd()
        paths = [directory / arg for arg in command if arg is not None]
        module_paths = set()
        if '-m' in command:
            index = command.index('-m') + 1
            if index < len(command):
                environment = dict(os.environ if environment is None else environment)
                pythonpath = os.fsdecode(environment.get(
                    'PYTHONPATH', environment.get(b'PYTHONPATH', b'')))
                # Respect src/ and other child search roots without importing
                # the package (which could execute its initialization).
                roots = [directory, *(directory / part for part in pythonpath.split(os.pathsep)),
                         *(directory / part for part in sys.path)]
                parts = str(command[index]).split('.')
                for base in roots:
                    module = base.joinpath(*parts)
                    module_paths.update([module / '__main__.py', module / '__main__' / '__init__.py'])
                    for level in range(1, len(parts) + 1):
                        prefix = base.joinpath(*parts[:level])
                        module_paths.update([prefix.with_suffix('.py'), prefix / '__init__.py'])
        module_paths = {Path(os.path.abspath(path)) for path in module_paths}
        paths.extend(module_paths)
        self.busy = True
        try:
            for path in paths:
                path = Path(os.path.abspath(path))
                try:
                    project_file = path.is_relative_to(self.root) and (
                        path in module_paths or path.is_file())
                except (OSError, ValueError):
                    continue  # Code strings and other argv values are not filenames.
                if project_file:
                    name = path.relative_to(self.root).as_posix()
                    if not EXCLUDED.intersection(Path(name).parts) and name not in REFERENCE_FILES:
                        self.observed.setdefault(self.consumer, {})[name] = fingerprint(
                            self.root, name, self.state['stats'])
        finally:
            self.busy = False

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_collection_modifyitems(self, items):
        for item in items:
            consumer = item.path.relative_to(self.root).as_posix()
            self.collected.add(consumer)
            if item.get_closest_marker('smart_always'):
                self.always.add(consumer)
        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_make_collect_report(self, collector):
        previous = self.consumer
        path = collector.path
        self.consumer = path.relative_to(self.root).as_posix() if (
            path.suffix == '.py' and path.is_relative_to(self.root)) else None
        yield
        self.consumer = previous

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef):
        previous = self.consumer
        if fixturedef.scope != 'function':
            self.consumer = '*'
        yield
        self.consumer = previous

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item):
        self.consumer = item.path.relative_to(self.root).as_posix()
        self.executed.add(self.consumer)
        self.busy = True
        try:
            for marker in item.iter_markers('smart_inputs'):
                for pattern in marker.args:
                    name = ('glob:' + pattern
                            if not pattern.startswith('version:')
                            and any(char in pattern for char in '*?[') else pattern)
                    self.observed.setdefault(self.consumer, {})[name] = fingerprint(
                        self.root, name, self.state['stats'])
        finally:
            self.busy = False
        yield
        self.consumer = None

    def pytest_sessionfinish(self, session, exitstatus):
        self.consumer = None
        receipt = os.environ.get('SMART_TESTING_SESSION')
        if receipt:
            Path(receipt).write_text(str(int(exitstatus)))
        if exitstatus not in (0, 5):
            return  # Failed consumers must remain stale and run again next time.
        self.state['always'] = sorted(consumer for consumer in (
            (set(self.state.get('always', [])) - self.collected) | self.always)
            if (self.root / consumer).is_file())
        if exitstatus == 5:
            save_state(self.path, self.state)
            return
        complete = os.environ.get('SMART_TESTING_COMPLETE')
        if complete == 'all':
            self.state['scope'] = os.environ['SMART_TESTING_SCOPE']
            self.state['pytest_environment'] = self.invocation
            self.state['inputs'] = {'*': self.observed.get('*', {})}
        if complete in {'all', 'modules'}:
            for consumer in self.executed:
                self.state['inputs'][consumer] = self.observed.get(consumer, {})
        for consumer, inputs in self.observed.items():
            if consumer == '*' or consumer in self.executed:
                self.state['inputs'].setdefault(consumer, {}).update(inputs)
        known = set().union(*(set(inputs) for inputs in self.state['inputs'].values()))
        for name in list(known):
            if name.startswith('glob:'):
                known.update(glob_members(self.root, name[5:]))
        self.state['stats'] = {name: stamp for name, stamp in self.state['stats'].items()
                               if name in known}
        save_state(self.path, self.state)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_load_initial_conftests(early_config):
    state_path = os.environ.get('SMART_TESTING_INPUTS')
    recorder = None
    if state_path:
        root = Path(os.environ.get('SMART_TESTING_ROOT', early_config.rootpath)).resolve()
        recorder = FileReads(root, Path(state_path))
        sys.addaudithook(recorder.audit)
        early_config.pluginmanager.register(recorder, 'smart-file-reads')
        recorder.consumer = '*'  # Initial conftest globals can feed any test.
    yield
    if recorder:
        recorder.consumer = None


def pytest_configure(config):
    config.addinivalue_line('markers', 'smart_always: run on every smart invocation (live external state)')
    config.addinivalue_line('markers', 'smart_inputs(*paths): additional file/glob or version:COMMAND inputs, including child reads')
    if not os.environ.get('SMART_TESTING_INPUTS'):
        return
    option = config.option
    incompatible = ('keyword', 'lf', 'stepwise', 'stepwise_skip', 'deselect',
                    'collectonly', 'ignore', 'ignore_glob', 'numprocesses',
                    'setuponly', 'setupplan', 'showfixtures', 'show_fixtures_per_test')
    narrowed = [name for name in incompatible if getattr(option, name, None)]
    if getattr(option, 'dist', 'no') != 'no':
        narrowed.append('dist')
    if narrowed:
        raise pytest.UsageError(
            'smart-test does not support partial or parallel pytest options: '
            + ', '.join(narrowed) + '; use the normal project check instead')
