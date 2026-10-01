"""Installed hook launchers report missing executables and run the guard."""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parent.parent
SHARED = json.loads((REPO / "settings.shared.json").read_text())


def _launcher_hooks():
    out = []
    for event, blocks in SHARED["hooks"].items():
        for block in blocks:
            for hook in block.get("hooks", []):
                if "$HOME/.local/bin/idh-hook" in hook.get("command", ""):
                    out.append((event, hook["command"]))
    return out


LAUNCHER_HOOKS = _launcher_hooks()


def test_every_launcher_hook_is_found():
    events = {event for event, _ in LAUNCHER_HOOKS}
    assert {"SessionStart", "SessionEnd", "PreToolUse"} <= events


@pytest.mark.parametrize("event,command", LAUNCHER_HOOKS)
def test_hook_checks_the_exact_script_before_running(event, command):
    script = "$HOME/.local/bin/idh-hook"
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
    assert "run <checkout>/bin/idh install from a plain terminal" in result.stderr


@pytest.mark.parametrize("event,command", LAUNCHER_HOOKS)
def test_missing_launcher_exits_2_with_the_repair(tmp_path, event, command):
    home = tmp_path / "home"
    home.mkdir()
    _assert_loud(_run(command, home, tmp_path), home)


@pytest.mark.parametrize("event,command", LAUNCHER_HOOKS)
def test_missing_launcher_under_an_existing_bin_dir_exits_2(tmp_path, event, command):
    """A scripts dir without the target: a -d check would exec and exit 127."""
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    _assert_loud(_run(command, home, tmp_path), home)


@pytest.mark.parametrize("event,command", LAUNCHER_HOOKS)
def test_non_executable_script_exits_2(tmp_path, event, command):
    """A present but non-executable script would otherwise exit 126."""
    home = tmp_path / "home"
    scripts = home / ".local" / "bin"
    scripts.mkdir(parents=True)
    name = "idh-hook"
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
    for _, command in LAUNCHER_HOOKS:
        assert gen.translate(command).startswith(gen.LAUNCHER), command
    smuggled = (
        '[ -x "$HOME/.local/bin/idh-hook" ] || { touch /tmp/pwn; echo "m" >&2; exit 2; }; '
        'exec "$HOME/.local/bin/idh-hook" x.sh'
    )
    assert gen.translate(smuggled) == smuggled
    substituted = (
        '[ -x "$HOME/.local/bin/idh-hook" ] || { echo "$(touch /tmp/pwn)" >&2; exit 2; }; '
        'exec "$HOME/.local/bin/idh-hook" x.sh'
    )
    assert gen.translate(substituted) == substituted


def test_installed_launcher_runs_the_guard(tmp_path):
    """Positive control: the installed launcher runs the real guard."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".local/bin").mkdir(parents=True)
    (home / ".local/bin/idh-hook").symlink_to(REPO / "adapters/claude-code/bin/idh-hook")
    repo = tmp_path / "repo"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git[:3], "init", "-q"], check=True)
    subprocess.run([*git, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "i"],
                   check=True)
    (repo / "f.txt").write_text("dirty\n")
    subprocess.run([*git[:3], "add", "f.txt"], check=True)
    (command,) = [c for e, c in LAUNCHER_HOOKS if e == "PreToolUse"]
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
