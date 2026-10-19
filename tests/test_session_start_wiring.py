"""Codex and Pi wire a session-start event to scripts/on-start-context.sh.

Both runtimes were measured on the installed versions (Codex 0.163.0, Pi 1.3.0):
the event fires and the text reaches the model. This pins the wiring so a
refactor of either adapter cannot drop it silently.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_codex_session_start_runs_on_start():
    doc = json.loads((REPO / "adapters/codex/hooks.json").read_text())
    commands = [
        hook["command"]
        for group in doc["hooks"]["SessionStart"]
        for hook in group["hooks"]
        if hook.get("type") == "command"
    ]
    assert any("idh-hook" in c and "on-start-context.sh" in c for c in commands), commands
    assert (REPO / "scripts/on-start-context.sh").is_file()


def test_pi_session_start_delivers_on_start_output():
    ext = (REPO / "adapters/pi/extensions/idh-guard.ts").read_text()
    assert 'pi.on("session_start"' in ext
    assert '"on-start-context.sh"' in ext
    assert 'deliverAs: "nextTurn"' in ext
    assert "delete env.CLAUDE_PROJECT_DIR" in ext


def test_claude_session_start_runs_context_and_sync_as_separate_hooks():
    doc = json.loads((REPO / "adapters/claude-code/hooks/hooks.json").read_text())
    commands = [
        hook["command"]
        for group in doc["hooks"]["SessionStart"]
        for hook in group["hooks"]
    ]
    assert any(c.endswith("idh-hook\" on-start-context.sh") for c in commands), commands
    assert any(c.endswith("idh-hook\" on-start-sync.sh") for c in commands), commands
    assert (REPO / "scripts/on-start-sync.sh").is_file()


def test_sync_hook_sets_hookspath_silently_and_is_inert_without_a_project(tmp_path):
    import subprocess

    from child_env import child_env

    script = REPO / "scripts/on-start-sync.sh"
    repo = tmp_path / "proj"
    (repo / "hooks").mkdir(parents=True)
    (repo / "hooks/pre-commit").write_text("#!/bin/sh\n")
    subprocess.run(["git", "init", "-q", str(repo)], check=True, env=child_env())

    env = child_env()
    env.pop("CLAUDE_PROJECT_DIR", None)
    bare = subprocess.run(["bash", str(script)], cwd=repo, env=env,
                          capture_output=True, text=True)
    assert bare.returncode == 0 and bare.stdout == ""
    hp = subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath"],
                        capture_output=True, text=True, env=child_env())
    assert hp.stdout.strip() == ""

    env["CLAUDE_PROJECT_DIR"] = str(repo)
    run = subprocess.run(["bash", str(script)], cwd=tmp_path, env=env,
                         capture_output=True, text=True)
    assert run.returncode == 0 and run.stdout == "" and run.stderr == ""
    hp = subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath"],
                        capture_output=True, text=True, env=child_env())
    assert hp.stdout.strip() == "hooks"
