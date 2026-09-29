"""Harness hooks fail loud when the ~/.idh pointer is missing (ticket 0982).

A hook command that names a missing script exits 127, which Claude Code
treats as non-blocking: the destructive-bash guard would vanish without a
word. Each pointer-dependent hook in settings.shared.json therefore checks
the pointer first and exits 2 with a message, which blocks a PreToolUse call
and surfaces on SessionStart/SessionEnd.
"""

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parent.parent
SHARED = json.loads((REPO / "settings.shared.json").read_text())


def _pointer_hooks():
    out = []
    for event, blocks in SHARED["hooks"].items():
        for block in blocks:
            for hook in block.get("hooks", []):
                if "$HOME/.idh" in hook.get("command", ""):
                    out.append((event, hook["command"]))
    return out


POINTER_HOOKS = _pointer_hooks()


def test_every_pointer_hook_is_found():
    events = {event for event, _ in POINTER_HOOKS}
    assert {"SessionStart", "SessionEnd", "PreToolUse"} <= events


@pytest.mark.parametrize("event,command", POINTER_HOOKS)
def test_hook_checks_the_pointer_before_running(event, command):
    assert command.startswith('[ -d "$HOME/.idh/scripts" ] || {'), command


def _guard_input(cwd: Path) -> str:
    return json.dumps({"tool_input": {"command": "git reset --hard"}, "cwd": str(cwd)})


@pytest.mark.parametrize("event,command", POINTER_HOOKS)
def test_missing_pointer_exits_2_with_a_message(tmp_path, event, command):
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(
        ["sh", "-c", command],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        input=_guard_input(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "~/.idh pointer is missing" in result.stderr


def test_wiring_links_through_the_pointer_stay_managed(tmp_path):
    """install-wirings.sh treats a link retargeted through ~/.idh as its own."""
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".idh").symlink_to(REPO, target_is_directory=True)
    link = home / ".codex" / "hooks.json"
    link.symlink_to(home / ".idh" / "adapters" / "codex" / "hooks.json")
    wirings = REPO / "adapters" / "install-wirings.sh"
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin"}

    def run(mode):
        return subprocess.run(["bash", str(wirings), mode], env=env, capture_output=True, text=True)

    installed = run("install")
    assert installed.returncode == 0, installed.stderr
    assert f"already discoverable: {link}" in installed.stdout
    removed = run("uninstall")
    assert removed.returncode == 0, removed.stderr
    assert not link.is_symlink()

    # Negative control: a link to some other file is still refused.
    link.parent.mkdir(parents=True, exist_ok=True)
    other = tmp_path / "other.json"
    other.write_text("{}")
    link.symlink_to(other)
    refused = run("install")
    assert refused.returncode == 1
    assert "REFUSED" in refused.stderr


def test_present_pointer_runs_the_guard(tmp_path):
    """Positive control: with the pointer in place the real guard decides."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".idh").symlink_to(REPO, target_is_directory=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git[:3], "init", "-q"], check=True)
    subprocess.run([*git, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "i"],
                   check=True)
    (repo / "f.txt").write_text("dirty\n")
    subprocess.run([*git[:3], "add", "f.txt"], check=True)
    (command,) = [c for e, c in POINTER_HOOKS if e == "PreToolUse"]
    result = subprocess.run(
        ["sh", "-c", command],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        input=_guard_input(repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr
    assert "pointer is missing" not in result.stderr
