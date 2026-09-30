"""Harness hooks fail loud when their script is unreachable (ticket 0982).

A hook command whose script is missing exits 127, or 126 when it is not
executable; Claude Code treats both as non-blocking, so the destructive-bash
guard would vanish without a word. Each pointer-dependent hook in
settings.shared.json therefore tests `-x` on the exact script it runs and
otherwise exits 2 with the repair command, which blocks a PreToolUse call
and surfaces on SessionStart/SessionEnd.
"""

import importlib.util
import json
import os
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
def test_hook_checks_the_exact_script_before_running(event, command):
    script = command.rsplit('exec "', 1)[1].split('"', 1)[0]
    assert command.startswith(f'[ -x "{script}" ] || {{'), command


def _guard_input(cwd: Path) -> str:
    return json.dumps({"tool_input": {"command": "git reset --hard"}, "cwd": str(cwd)})


def _run(command: str, home: Path, cwd: Path):
    return subprocess.run(
        ["sh", "-c", command],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        input=_guard_input(cwd),
        capture_output=True,
        text=True,
    )


def _assert_loud(result, home: Path):
    assert result.returncode == 2
    assert "Restore the checkout at ~/.idh from a plain terminal outside Claude/Codex" in result.stderr


@pytest.mark.parametrize("event,command", POINTER_HOOKS)
def test_missing_pointer_exits_2_with_the_repair(tmp_path, event, command):
    home = tmp_path / "home"
    home.mkdir()
    _assert_loud(_run(command, home, tmp_path), home)


@pytest.mark.parametrize("event,command", POINTER_HOOKS)
def test_missing_script_under_a_present_pointer_exits_2(tmp_path, event, command):
    """A scripts dir without the target: a -d check would exec and exit 127."""
    home = tmp_path / "home"
    (home / ".idh" / "scripts").mkdir(parents=True)
    _assert_loud(_run(command, home, tmp_path), home)


@pytest.mark.parametrize("event,command", POINTER_HOOKS)
def test_non_executable_script_exits_2(tmp_path, event, command):
    """A present but non-executable script would otherwise exit 126."""
    home = tmp_path / "home"
    scripts = home / ".idh" / "scripts"
    scripts.mkdir(parents=True)
    name = command.rsplit("/scripts/", 1)[1].split('"', 1)[0]
    (scripts / name).write_text("#!/bin/sh\nexit 0\n")
    os.chmod(scripts / name, 0o644)
    _assert_loud(_run(command, home, tmp_path), home)


def _generator():
    path = REPO / "scripts" / "gen-claude-code-adapter-hooks.py"
    spec = importlib.util.spec_from_file_location("gen_hooks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_translates_only_the_exact_checked_form():
    gen = _generator()
    for _, command in POINTER_HOOKS:
        assert gen.translate(command).startswith(gen.LAUNCHER), command
    smuggled = (
        '[ -x "$HOME/.idh/scripts/x.sh" ] || { touch /tmp/pwn; echo "m" >&2; exit 2; }; '
        'exec "$HOME/.idh/scripts/x.sh"'
    )
    assert gen.translate(smuggled) == smuggled
    substituted = (
        '[ -x "$HOME/.idh/scripts/x.sh" ] || { echo "$(touch /tmp/pwn)" >&2; exit 2; }; '
        'exec "$HOME/.idh/scripts/x.sh"'
    )
    assert gen.translate(substituted) == substituted


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
    assert "plain terminal" not in result.stderr
