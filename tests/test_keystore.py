"""The shared provider reader retains the retired executor's credential guards.

All values are fake; subprocesses use disposable files and an allowlisted
environment. No live keys or models are accessed.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / 'scripts' / 'keystore.py'
NAME = 'ANTHROPIC_API_KEY'
SENTINEL = 'FAKE-KEYSTORE-SENTINEL-1205-not-a-real-key'
CONTROL = 'KEYSTORE-1205-HAYSTACK-CONTROL'
CHILD = '''
import importlib.util
import sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("keystore_under_test", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
value = mod.keystore_value(Path(sys.argv[2]), sys.argv[3])
print("KEYSTORE-1205-HAYSTACK-CONTROL")
print("unreadable" if value is None else "resolved_length=%d" % len(value))
'''


def read_child(tmp_path, content, *, name=NAME, extra_env=None):
    provider = tmp_path / 'provider.env'
    if content is not None:
        provider.write_bytes(content)
    return subprocess.run(
        [sys.executable, '-S', '-c', CHILD, str(SCRIPT), str(provider), name],
        env={'PATH': os.defpath, **(extra_env or {})},
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )


@pytest.mark.integration
@pytest.mark.parametrize('ending', [b'\n', b'\r\n', b'\nfalse\n', b'\nexit 7\n'])
def test_scalar_resolution_without_leaking_or_sdk(tmp_path, ending):
    proc = read_child(tmp_path, f"export {NAME}='{SENTINEL}'".encode() + ending)
    assert proc.returncode == 0, proc.stderr
    output = proc.stdout + proc.stderr
    assert CONTROL in output, 'empty output would make the no-leak check vacuous'
    assert SENTINEL not in output
    assert f'resolved_length={len(SENTINEL)}' in proc.stdout


@pytest.mark.integration
def test_bare_assignment_and_quotes_are_shell_values(tmp_path):
    proc = read_child(tmp_path, f'{NAME}="{SENTINEL}"\n'.encode())
    assert proc.returncode == 0
    assert f'resolved_length={len(SENTINEL)}' in proc.stdout
    assert SENTINEL not in proc.stdout + proc.stderr


@pytest.mark.integration
@pytest.mark.parametrize('content', [
    None,
    b'# no credential\n',
    f'{NAME}=(first second)\n'.encode(),
    b'export ' + NAME.encode() + b"='fake-\xff-sentinel'\n",
    f"{NAME}='first\nsecond'\n".encode(),
    f"{NAME}='first\rsecond'\n".encode(),
])
def test_unreadable_or_non_scalar_values_are_explicitly_missing(tmp_path, content):
    proc = read_child(tmp_path, content)
    assert proc.returncode == 0, proc.stderr
    assert CONTROL in proc.stdout
    assert 'unreadable' in proc.stdout
    assert 'UnicodeDecodeError' not in proc.stderr


@pytest.mark.integration
def test_oversized_provider_is_rejected_before_execution(tmp_path):
    marker = tmp_path / 'must-not-exist'
    content = f"touch '{marker}'\n{NAME}='{SENTINEL}'\n".encode() + b'#' * 270_000
    proc = read_child(tmp_path, content)
    assert proc.returncode == 0
    assert 'unreadable' in proc.stdout
    assert not marker.exists()
    assert SENTINEL not in proc.stdout + proc.stderr


@pytest.mark.integration
def test_clean_shell_does_not_inherit_credentials_or_bash_env(tmp_path):
    marker = tmp_path / 'must-not-exist'
    startup = tmp_path / 'startup.sh'
    startup.write_text(f"touch '{marker}'\n")
    proc = read_child(tmp_path, b'# absent here\n', extra_env={
        NAME: SENTINEL, 'BASH_ENV': str(startup),
    })
    assert proc.returncode == 0
    assert 'unreadable' in proc.stdout
    assert not marker.exists()
    assert SENTINEL not in proc.stdout + proc.stderr


@pytest.mark.integration
@pytest.mark.parametrize('name', ['PATH', 'X"; echo INJECTED; #'])
def test_rejects_names_before_sourcing(tmp_path, name):
    marker = tmp_path / 'must-not-exist'
    proc = read_child(tmp_path, f"touch '{marker}'\n".encode(), name=name)
    assert proc.returncode != 0
    assert 'not an allowed credential name' in proc.stderr
    assert not marker.exists()
    assert 'INJECTED' not in proc.stdout
