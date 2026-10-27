"""Child env for test subprocesses: `os.environ` with the bash loader off.

Ticket 0940. The harness points `BASH_ENV` at `scripts/bash-env.sh`, which
re-runs the project `.env` parser in every child bash. A test that spawns a
subprocess without an `env=` inherits that variable, so the child re-enters
the credential loader at startup — the exact 2026-07-27 defect class: a
fixture credential is overridden by the real one inside the child, and a
failing assertion prints what it found.

The accepted remedy (rules/coding-bash.md) is to pass every test child an env
that does not carry `BASH_ENV`. `child_env()` is that env: the parent's live
environment minus the loader variable, so `monkeypatch.setenv` fixtures and
ambient `PATH`/`HOME` still reach the child, while `bash` children start with
no loader. For a fully known-empty base, build the dict from scratch instead
(tests/test_on_end_hook.py is the reference).
"""

import os

CLEARED_KEYS = ("BASH_ENV",)


def child_env() -> dict[str, str]:
    """`os.environ` at call time, minus the bash loader variables."""
    return {k: v for k, v in os.environ.items() if k not in CLEARED_KEYS}


SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"


def isolated_path() -> str:
    """PATH for an install test: system directories only.

    `idh install` refuses a command name that `shutil.which` already finds on
    PATH (ticket 1257). A test that isolates HOME but inherits PATH sees the
    developer's real `~/.local/bin` links and refuses on that machine only.
    """
    return SYSTEM_PATH
