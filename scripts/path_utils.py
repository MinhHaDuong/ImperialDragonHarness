#!/usr/bin/env python3
"""Shared helpers for the hook scripts.

Home of ``contained()``, used by every hook that builds a filesystem path from a
value a project controls (a manifest field, a sniffed ``\\documentclass``), and
of ``hook_strict()``, which decides whether a hook's entry point may re-raise.
Both ``knowledge_hints.py`` and ``inject_rule_on_edit.py`` import them from here
so each is written once, not copied — a copy drifts, and a drifted copy of a
security check is worse than none.
"""

import os
from pathlib import Path


def contained(root: Path, rel: str) -> Path | None:
    """Resolve `rel` under `root`, or None when it escapes.

    `Path("/repo") / "/etc/passwd"` is `/etc/passwd`: the left operand is
    discarded the moment the right is absolute, and `../../..` walks out just as
    easily. Existence alone is therefore not the check it looks like. What these
    hooks emit is injected into the model's context, so an uncontained path
    turns a manifest -- merged once, perhaps without the traversal being noticed
    in review -- into a durable instruction to read an arbitrary file, on every
    session and every prompt thereafter.
    """
    try:
        root_r = root.resolve()
        target = (root_r / rel).resolve()
    except (OSError, ValueError, RuntimeError):
        return None
    return target if target.is_relative_to(root_r) else None


STRICT_ENV = "IDH_HOOK_STRICT"


def hook_strict() -> bool:
    """True when a hook entry point was asked to re-raise instead of swallowing.

    Both hooks wrap ``main()`` in ``except (Exception, SystemExit)`` and then
    exit 0. In production that is right: an advisory hook must never block the
    tool, and the prompt channel has no shell wrapper to absorb a traceback. But
    on the only two channels a subprocess-driven test can observe — exit code
    and stdout — a total crash and a correct silent no-op are then byte for byte
    identical, so *every* test whose expectation is "silent" is satisfied by
    total breakage. Measured 2026-08-26 by making the entry points raise
    unconditionally: 14 of 26 CLI-driven tests of ``knowledge_hints`` and 3 of 5
    of ``inject_rule_on_edit`` still passed, among them both guards against
    exfiltration into the model's context (ticket 0610).

    This flag is the only thing that tells the two apart. It is off unless the
    variable is exactly ``"1"``, so production behaviour is unchanged; nothing
    in the harness sets it, and ``tests/test_hook_failures_are_visible.py``
    asserts that no production surface does.
    """
    return os.environ.get(STRICT_ENV) == "1"
