"""Pin that beat-settings.json's PreToolUse hook commands resolve at runtime.

Background: ticket 0322 (PR #570) rewrote the destructive-bash guard hook path
in scripts/beat-settings.json from a hardcoded home literal to the agnostic
`$HOME/.claude/...` form so it would pass the agnostic gate on scripts/. The
agnostic gate pins the *textual* form; nothing verified the path still
*resolves* to a real executable once `$HOME` is expanded.

This test loads beat-settings.json, walks every PreToolUse hook command
generically, expands environment variables, and asserts the target is an
existing executable file. It is a static resolvability check: it does not
exercise the hook runner's dispatch (that behavior is settled by the live
production settings.json, which wires the identical `$HOME/...` command form and
whose guards fire every session). If `$HOME` expansion ever regresses to an
unresolvable literal, this test goes RED.
"""

import json
import os
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
BEAT_SETTINGS = REPO_ROOT / "scripts" / "beat-settings.json"


def _pretooluse_commands() -> list[str]:
    """Every PreToolUse hook `command` string in beat-settings.json."""
    settings = json.loads(BEAT_SETTINGS.read_text())
    commands: list[str] = []
    for entry in settings.get("hooks", {}).get("PreToolUse", []):
        for hook in entry.get("hooks", []):
            command = hook.get("command")
            if command is not None:
                commands.append(command)
    return commands


def test_beat_settings_hook_resolves() -> None:
    """Each PreToolUse hook command resolves to an existing executable."""
    commands = _pretooluse_commands()

    # Non-vacuity guard: a malformed or empty JSON must not pass silently.
    assert commands, (
        f"no PreToolUse hook commands found in {BEAT_SETTINGS} — "
        "malformed JSON or the hook block was removed"
    )

    for command in commands:
        resolved = Path(os.path.expandvars(command))
        assert resolved.is_file(), (
            f"hook command {command!r} expands to {resolved}, which does not exist"
        )
        assert os.access(resolved, os.X_OK), (
            f"hook command {command!r} expands to {resolved}, which is not executable"
        )
