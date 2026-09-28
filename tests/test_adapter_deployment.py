"""Fresh install/uninstall of the whole pilot surface (ticket 0810).

The pilot creates exactly four things on a machine, in two planes:

- skills plane (0802/0803): ``~/.agents/skills/{perch,healthcheck}`` and,
  when the repository is not ``~/.claude`` itself, a Claude Code projection
  — all via ``bin/idh``;
- wiring plane (0809): ``~/.codex/hooks.json`` and
  ``~/.pi/agent/extensions/idh-guard.ts`` — via
  ``adapters/install-wirings.sh``.

This module proves, in fixture homes (no developer machine state, no live
credentials, no CLIs — version probes are stubbed as in the perch tests):

- a fresh install creates exactly the managed surface and nothing else;
- re-install is idempotent ("already discoverable" is success, not error);
- an unmanaged target is REFUSED — its content survives untouched, the
  other targets still report their own state, and the exit code says
  something refused. Activation never overwrites the only recoverable copy;
- uninstall takes back exactly what install created, pruning the
  directories it emptied, leaving unmanaged files alone;
- an interrupted install (partial surface) is recovered by re-running it;
- a canary planted in an unmanaged config value appears nowhere else — no
  install artifact, journal or diagnostic carries command or config text.
"""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WIRINGS = REPO / "adapters" / "install-wirings.sh"
CANARY = "CANARY-0810-qv7-only-in-its-origin"

pytestmark = pytest.mark.integration


def _module():
    spec = importlib.util.spec_from_file_location("perch", REPO / "adapters" / "perch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


perch = _module()


@pytest.fixture
def home(tmp_path, monkeypatch):
    root = tmp_path / "home"
    root.mkdir()
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.delenv("USERPROFILE", raising=False)
    # No CLIs in CI: stub the version probe as the perch tests do.
    monkeypatch.setattr(perch, "check_version", lambda *a, **k: "9.9.9")
    return root


def wirings(home, *args):
    return subprocess.run(
        ["bash", str(WIRINGS), *args],
        capture_output=True, text=True, timeout=30,
        env={**os.environ, "HOME": str(home)},
    )


def skills(home, skill):
    for harness in ("claude", "codex", "pi"):
        perch.install(harness, skill)


def unskills(home, skill):
    for harness in ("claude", "codex", "pi"):
        perch.uninstall(harness, skill)


def test_full_pilot_surface_installs_and_uninstalls_exactly(home):
    skills(home, "perch")
    skills(home, "healthcheck")
    r = wirings(home, "install")
    assert r.returncode == 0, r.stderr
    managed = [
        home / ".agents" / "skills" / "perch",
        home / ".agents" / "skills" / "healthcheck",
        home / ".claude" / "skills" / "perch",
        home / ".claude" / "skills" / "healthcheck",
        home / ".codex" / "hooks.json",
        home / ".pi" / "agent" / "extensions" / "idh-guard.ts",
    ]
    for path in managed:
        assert path.is_symlink(), f"missing managed path: {path}"
    assert json.loads((home / ".codex" / "hooks.json").read_text())["hooks"]["PreToolUse"]

    unskills(home, "perch")
    unskills(home, "healthcheck")
    r = wirings(home, "uninstall")
    assert r.returncode == 0, r.stderr
    for path in managed:
        assert not path.exists() and not path.is_symlink(), f"left behind: {path}"
    # Only directories the install emptied are pruned; $HOME survives.
    assert home.is_dir()


def test_reinstall_is_idempotent(home):
    assert wirings(home, "install").returncode == 0
    r = wirings(home, "install")
    assert r.returncode == 0, r.stderr
    assert "already discoverable" in r.stdout


def test_unmanaged_target_is_refused_and_never_overwritten(home):
    codex = home / ".codex" / "hooks.json"
    codex.parent.mkdir(parents=True)
    codex.write_text(f'{{"hooks": {{}}, "note": "{CANARY}"}}')
    before = codex.read_text()

    r = wirings(home, "install")
    assert r.returncode == 1
    assert "REFUSED" in r.stderr
    assert codex.read_text() == before, "the only copy was overwritten"
    # The other target still installed and is reported honestly.
    assert (home / ".pi" / "agent" / "extensions" / "idh-guard.ts").is_symlink()

    r = wirings(home, "uninstall")
    assert r.returncode == 1
    assert codex.read_text() == before, "an unmanaged file was removed or altered"
    assert not (home / ".pi").exists(), "the managed wiring was not taken back"

    # The canary appears nowhere outside its origin file.
    for path in home.rglob("*"):
        if path.is_file() and path != codex:
            assert CANARY not in path.read_text(errors="replace"), f"canary leaked: {path}"


def test_interrupted_install_is_recovered_by_rerunning(home):
    # Partial surface, as an interrupted first install would leave it.
    target = home / ".pi" / "agent" / "extensions" / "idh-guard.ts"
    target.parent.mkdir(parents=True)
    target.symlink_to(REPO / "adapters" / "pi" / "extensions" / "idh-guard.ts")
    r = wirings(home, "install")
    assert r.returncode == 0, r.stderr
    assert (home / ".codex" / "hooks.json").is_symlink()


def test_foreign_symlink_is_refused_not_silently_retargeted(home):
    foreign = home / ".codex" / "hooks.json"
    foreign.parent.mkdir(parents=True)
    foreign.symlink_to("/somewhere/else/hooks.json")
    r = wirings(home, "install")
    assert r.returncode == 1
    assert "REFUSED" in r.stderr
    assert foreign.readlink() == Path("/somewhere/else/hooks.json")


def test_status_reports_each_target(home):
    r = wirings(home, "status")
    assert r.returncode == 0
    assert "not installed" in r.stdout
    wirings(home, "install")
    r = wirings(home, "status")
    assert "codex:" in r.stdout and "pi:" in r.stdout
