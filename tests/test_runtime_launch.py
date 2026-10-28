"""Ticket 1313: runtime.py `launch` verb (can only): configured doors, never availability."""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import runtime  # noqa: E402
import runtime_launch  # noqa: E402


def stub_path(tmp_path, *names):
    for n in names:
        f = tmp_path / n
        f.write_text("#!/bin/sh\n")
        f.chmod(0o755)
    return {"PATH": str(tmp_path)}


def test_pi_cannot_launch_subagent(capsys):
    rc = runtime.main(["--runtime", "pi", "can", "launch.subagent"])
    assert rc == 1 and "Pi core has no subagents" in capsys.readouterr().out


def test_claude_and_codex_can_launch_subagent(capsys):
    assert runtime.main(["--runtime", "claude", "can", "launch.subagent"]) == 0
    assert runtime.main(["--runtime", "codex", "can", "launch"]) == 0
    assert "YES launch codex" in capsys.readouterr().out


def test_headless_door_with_program_on_path(tmp_path):
    env = stub_path(tmp_path, "codex")
    assert runtime_launch.can("pi", "headless.codex", env) is None


def test_headless_door_program_absent_exits_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PATH", str(tmp_path))
    rc = runtime.main(["--runtime", "claude", "can", "launch.headless.codex"])
    assert rc == 1 and "codex is not on PATH" in capsys.readouterr().out


def test_unknown_door_and_mode(tmp_path):
    env = stub_path(tmp_path)
    assert "no headless door" in runtime_launch.can("claude", "headless.nope", env)
    assert "no launch mode" in runtime_launch.can("claude", "bogus", env)


def test_launch_registered_and_run_is_noop(capsys):
    assert runtime_launch in runtime.VERBS
    assert runtime.main(["--runtime", "claude", "launch"]) == 1
