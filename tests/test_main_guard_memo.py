"""Lair's main-update guard memo (ticket 1180).

While ticket 1180 is open, /lair carries one line read from the main-update
journal of the clone: updates of main in the last day, warned and refused
counts, the current idh.mainGuard value. The script runs here on a scratch
repository with a hand-written journal; git itself is real.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "main_guard_memo.py"
NOW = "2026-10-21T18:00:00Z"


def _env():
    env = {k: v for k, v in child_env().items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    return env


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=_env())
    return tmp_path


def _journal(repo: Path) -> Path:
    return repo / ".git" / "idh" / "main-journal.jsonl"


def _write(repo: Path, entries: list) -> None:
    path = _journal(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [e if isinstance(e, str) else json.dumps(e) for e in entries]
    path.write_text("".join(line + "\n" for line in lines))


def _update(time: str, action: str = "allowed") -> list:
    """The two lines the hook writes for one update of main that went through."""
    decision = "not-gated" if action != "allowed" else "on-origin"
    return [
        {"time": time, "phase": "prepared", "decision": decision, "action": action},
        {"time": time, "phase": "committed", "decision": "", "action": ""},
    ]


def _set_mode(repo: Path, value: str) -> None:
    subprocess.run(["git", "-C", str(repo), "config", "idh.mainGuard", value],
                   check=True, env=_env())


def _memo(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), "--now", NOW, *extra],
        capture_output=True, text=True, env=_env(), check=False)
    assert result.returncode == 0, result.stderr
    return result


def test_counts_updates_and_warned_in_the_last_day(repo):
    _write(repo, _update("2026-10-21T10:00:00Z")
           + _update("2026-10-21T12:00:00Z", "warned")
           + _update("2026-10-21T17:59:00Z"))
    out = _memo(repo).stdout
    assert len(out.splitlines()) == 1
    assert "3 updates of main" in out
    assert "1 warned" in out
    assert "idh.mainGuard=warn (unset)" in out
    assert "1180" in out


def test_entries_older_than_the_window_are_not_counted(repo):
    _write(repo, _update("2026-10-20T17:59:00Z", "warned")
           + _update("2026-10-20T18:01:00Z"))
    out = _memo(repo).stdout
    assert "1 updates of main" in out
    assert "0 warned" in out


def test_window_is_a_parameter(repo):
    _write(repo, _update("2026-10-20T12:00:00Z") + _update("2026-10-21T17:00:00Z"))
    assert "2 updates of main in the last 48 h" in _memo(repo, "--hours", "48").stdout


def test_explicit_warn_and_off_are_reported(repo):
    _write(repo, _update("2026-10-21T17:00:00Z"))
    _set_mode(repo, "warn")
    assert "idh.mainGuard=warn;" in _memo(repo).stdout
    _set_mode(repo, "off")
    out = _memo(repo).stdout
    assert "idh.mainGuard=off" in out and "1180" in out


def test_enforce_with_nothing_refused_prints_nothing(repo):
    _write(repo, _update("2026-10-21T17:00:00Z"))
    _set_mode(repo, "enforce")
    assert _memo(repo).stdout == ""


def test_enforce_with_a_refusal_prints_the_line(repo):
    _write(repo, _update("2026-10-21T17:00:00Z")
           + [{"time": "2026-10-21T17:30:00Z", "phase": "prepared",
               "decision": "not-gated", "action": "refused"},
              {"time": "2026-10-21T17:30:00Z", "phase": "aborted",
               "decision": "", "action": ""}])
    _set_mode(repo, "enforce")
    out = _memo(repo).stdout
    assert "1 updates of main" in out
    assert "1 refused" in out
    assert "idh.mainGuard=enforce" in out


def test_missing_journal_is_never_silent(repo):
    out = _memo(repo).stdout
    assert out.startswith("main-guard: not checked")
    assert "hook may not be running" in out
    _set_mode(repo, "enforce")
    assert _memo(repo).stdout.startswith("main-guard: not checked")


def test_unreadable_journal_is_never_silent(repo):
    _write(repo, _update("2026-10-21T17:00:00Z"))
    _journal(repo).chmod(0)
    try:
        if _can_read(_journal(repo)):
            pytest.skip("running with privileges that read a mode-0 file")
        assert _memo(repo).stdout.startswith("main-guard: not checked")
    finally:
        _journal(repo).chmod(0o644)


def _can_read(path: Path) -> bool:
    try:
        path.read_bytes()
    except OSError:
        return False
    return True


def test_unreadable_lines_are_skipped_and_counted(repo):
    _write(repo, _update("2026-10-21T17:00:00Z")
           + ["{not json", '{"phase": "committed", "time": "yesterday"}'])
    out = _memo(repo).stdout
    assert "1 updates of main" in out
    assert "2 unreadable lines skipped" in out


def test_outside_a_repository_is_never_silent(tmp_path):
    out = _memo(tmp_path / "nowhere").stdout
    assert out.startswith("main-guard: not checked")
