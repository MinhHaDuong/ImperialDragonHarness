"""Fresh install of the whole pilot surface (tickets 0810, 0987).

The pilot surface is four links, in two planes:

- skills plane (0802/0803): ``~/.agents/skills/{perch,healthcheck}`` and,
  when the repository is not ``~/.claude`` itself, a Claude Code projection
  — all via ``bin/idh``;
- wiring plane (0809): ``~/.codex/hooks.json`` and
  ``~/.pi/agent/extensions/idh-guard.ts`` — via ``idh install``
  (``adapters/lifecycle.py``, ticket 0987), from adapters/projections.json.

This module proves, in fixture homes (no developer machine state, no live
credentials, no CLIs — version probes are stubbed as in the perch tests):

- a fresh install creates the managed surface;
- re-install is idempotent (a correct link is success, not error);
- an unmanaged target is refused — its content survives untouched, the
  other targets still install, and the exit code says something refused.
  Activation never overwrites the only recoverable copy;
- skill uninstall takes back what skill install created;
- an interrupted install (partial surface) is recovered by re-running it;
- a canary planted in an unmanaged config value appears nowhere else — no
  install artifact or diagnostic carries config text.
"""

import importlib.util
import json
from pathlib import Path

import pytest
from tracked_tree import tracked_checkout

# The tracked tree, not this checkout: untracked links here (the private
# overlay) would reach $IDH_ROOT and fail the run on one machine only (0989).
REPO = tracked_checkout()
CANARY = "CANARY-0810-qv7-only-in-its-origin"

pytestmark = pytest.mark.integration


def _module(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "adapters" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


perch = _module("perch")
lifecycle = _module("lifecycle")


@pytest.fixture
def home(tmp_path, monkeypatch):
    root = tmp_path / "home"
    root.mkdir()
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.delenv("USERPROFILE", raising=False)
    # No CLIs in CI: stub the version probe as the perch tests do.
    monkeypatch.setattr(perch, "check_version", lambda *a, **k: "9.9.9")
    return root


def wirings():
    """The link half of `idh install`; the loader and timers are tested apart."""
    return lifecycle.install_links()


def test_full_pilot_surface_installs_and_skills_uninstall(home):
    # Links first: ~/.claude becomes the checkout, as on a real machine.
    assert wirings() == 0
    for skill in ("perch", "healthcheck"):
        for harness in ("claude", "codex", "pi"):
            perch.install(harness, skill)
    managed = [
        home / ".agents" / "skills" / "perch",
        home / ".agents" / "skills" / "healthcheck",
        home / ".pi" / "agent" / "extensions" / "idh-guard.ts",
    ]
    for path in managed:
        assert path.is_symlink(), f"missing managed path: {path}"
    assert (home / ".claude" / "skills" / "perch").resolve() == REPO / "skills" / "perch"
    assert json.loads((home / ".codex" / "hooks.json").read_text())["hooks"]["PreToolUse"]

    for skill in ("perch", "healthcheck"):
        for harness in ("claude", "codex", "pi"):
            perch.uninstall(harness, skill)
    assert not (home / ".agents" / "skills" / "perch").is_symlink()
    assert (REPO / "skills" / "perch" / "SKILL.md").is_file(), "canonical source touched"


def test_reinstall_is_idempotent(home, capsys):
    assert wirings() == 0
    capsys.readouterr()
    assert wirings() == 0
    assert "installed:" not in capsys.readouterr().out


def test_unmanaged_target_is_refused_and_never_overwritten(home, capsys):
    codex = home / ".codex" / "hooks.json"
    codex.parent.mkdir(parents=True)
    codex.write_text(f'{{"hooks": [], "note": "{CANARY}"}}')
    before = codex.read_text()

    assert wirings() == 1
    assert f"REFUSED: {codex}" in capsys.readouterr().err
    assert codex.read_text() == before, "the only copy was overwritten"
    # The other target still installed.
    assert (home / ".pi" / "agent" / "extensions" / "idh-guard.ts").is_symlink()

    # The canary appears nowhere outside its origin file (links into the
    # checkout are not followed: they are the repository, not install output).
    for path in home.rglob("*"):
        if path.is_file() and not path.is_symlink() and path != codex:
            assert CANARY not in path.read_text(errors="replace"), f"canary leaked: {path}"


def test_interrupted_install_is_recovered_by_rerunning(home):
    # Partial surface, as an interrupted first install would leave it.
    target = home / ".pi" / "agent" / "extensions" / "idh-guard.ts"
    target.parent.mkdir(parents=True)
    target.symlink_to(REPO / "adapters" / "pi" / "extensions" / "idh-guard.ts")
    assert wirings() == 0
    assert (home / ".codex" / "hooks.json").is_file()


def test_foreign_symlink_is_refused_not_silently_retargeted(home, capsys):
    foreign = home / ".codex" / "hooks.json"
    foreign.parent.mkdir(parents=True)
    foreign.symlink_to("/somewhere/else/hooks.json")
    assert wirings() == 1
    assert f"MISSING: {foreign}" in capsys.readouterr().err
    assert foreign.readlink() == Path("/somewhere/else/hooks.json")
