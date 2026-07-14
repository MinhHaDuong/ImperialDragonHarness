"""Pin that beat-settings.json's PreToolUse hook commands name real scripts.

Background: ticket 0322 (PR #570) rewrote the destructive-bash guard hook path
in scripts/beat-settings.json from a hardcoded home literal to the agnostic
`$HOME/.claude/...` form so it would pass the agnostic gate on scripts/. The
agnostic gate pins the *textual* form; nothing verified the path still names a
real executable once the command is resolved.

This test loads beat-settings.json, walks every PreToolUse hook command
generically, and asserts the target is an existing executable file. Resolution
is hermetic — rooted in THIS checkout, not the machine's live `$HOME`. In
production the harness IS installed at `$HOME/.claude`, so a command under the
`$HOME/.claude/` prefix maps onto the repo root computed from `__file__`; the
check rebuilds such commands against REPO_ROOT before testing them. That makes
the test portable: it passes in the author's install, in CI (where `$HOME` is
the runner's home and the checkout lives elsewhere), and in any clone. It is a
static resolvability check: it does not exercise the hook runner's dispatch
(that behavior is settled by the live production settings.json, which wires the
identical `$HOME/...` command form and whose guards fire every session). If a
hook command ever names a script missing from the checkout, this test goes RED.
"""

import json
import os
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
BEAT_SETTINGS = REPO_ROOT / "scripts" / "beat-settings.json"

# In production the harness IS installed at $HOME/.claude, so a command under
# this prefix names a file that lives at REPO_ROOT in the checkout under test.
HARNESS_INSTALL_PREFIX = Path.home() / ".claude"


def _resolve(command: str) -> Path:
    """Resolve a hook command against THIS checkout, not the live $HOME.

    Expand environment variables, then remap any path under the harness install
    prefix ($HOME/.claude/...) onto REPO_ROOT so the check verifies the named
    script exists in this repo — hermetic and portable across CI and clones.
    """
    expanded = Path(os.path.expandvars(command))
    try:
        relative = expanded.relative_to(HARNESS_INSTALL_PREFIX)
    except ValueError:
        return expanded
    return REPO_ROOT / relative


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
        resolved = _resolve(command)
        assert resolved.is_file(), (
            f"hook command {command!r} expands to {resolved}, which does not exist"
        )
        assert os.access(resolved, os.X_OK), (
            f"hook command {command!r} expands to {resolved}, which is not executable"
        )
