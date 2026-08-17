#!/usr/bin/env python3
"""Shared prose/code routing predicate for the review skills (ticket 0550).

A changed file is a *manuscript* iff the axis resolver yields a ``doctype``
for it — from the project manifest (``<repo>/.claude/rules-map.toml``) or,
when no manifest maps it, from the ``\\documentclass`` sniff. Format alone is
NOT the discriminant: process prose (conception notes, ``.erg`` tickets)
resolves to no doctype and stays on the code panel — the 2026-08-17 audit
measured that the code lenses served exactly those diffs correctly.

The axis model has a single source, ``scripts/inject_rule_on_edit.py``
(rules/README.md § Per-file rule injection); this module loads it instead of
re-deriving extensions or globs (ticket 0531 documents what a diverging
re-extraction costs).

CLI: ``prose_predicate.py FILE [FILE ...]`` prints ``prose`` when any file is
a manuscript (any-semantics: one manuscript flips a mixed diff), else
``code``. Exit code 0 either way, so ``set -e`` callers capture the word
without a guard. A path that does not exist from the cwd is refused (exit 2,
no verdict): the predicate reads the disk, so a parked cwd would otherwise
return a plausible, wrong ``code`` — the exact failure mode ticket 0550
closes. A refusal is a cwd error to fix, never an answer.
"""

import argparse
import importlib.util
from pathlib import Path
from types import ModuleType

_RESOLVER_PATH = Path(__file__).resolve().parent / "inject_rule_on_edit.py"
_resolver: ModuleType | None = None


def _load_resolver() -> ModuleType:
    global _resolver
    if _resolver is None:
        spec = importlib.util.spec_from_file_location(
            "inject_rule_on_edit", _RESOLVER_PATH
        )
        assert spec is not None and spec.loader is not None, _RESOLVER_PATH
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _resolver = mod
    return _resolver


def is_manuscript(path: str) -> bool:
    """True iff the file resolves to a doctype — a rendered deliverable."""
    return "doctype" in _load_resolver().resolve_axes(path)


def diff_is_prose(paths: list[str]) -> bool:
    """Any-semantics over a diff's changed files: one manuscript flips it."""
    return any(is_manuscript(p) for p in paths)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Route a diff to the prose or code review panel: "
        "prints 'prose' if any file resolves to a doctype, else 'code'."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="changed file paths (absolute, or relative to the checkout cwd)",
    )
    args = parser.parse_args()
    missing = [f for f in args.files if not Path(f).exists()]
    if missing:
        parser.error(
            f"path(s) not found from cwd {Path.cwd()}: {', '.join(missing)} — "
            "anchor the cwd in the checkout that holds the diff; answering "
            "'code' here would be a plausible, wrong verdict"
        )
    print("prose" if diff_is_prose(args.files) else "code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
