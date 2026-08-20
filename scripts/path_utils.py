#!/usr/bin/env python3
"""Shared path helpers for the hook scripts.

Home of ``contained()``, used by every hook that builds a filesystem path from a
value a project controls (a manifest field, a sniffed ``\\documentclass``). Both
``knowledge_hints.py`` and ``inject_rule_on_edit.py`` import it from here so the
containment check is written once, not copied — a copy drifts, and a drifted
copy of a security check is worse than none.
"""

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
