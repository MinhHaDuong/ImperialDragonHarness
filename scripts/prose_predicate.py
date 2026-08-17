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

``--axes`` prints the resolved doctype and language per file instead of the
verdict. Routing picks *which panel* reviews a diff; the axes tell a reviewer
*which rulebook* to hold it to. Agent B had neither, and guessed: it checked a
manuscript against ``rules/doctype/book.md`` where the manifest declares
``techreport`` (audit of 2026-08-17, MR 136).
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


def axes_for(path: str) -> dict[str, str]:
    """The file's resolved axes — which house rulebooks apply to it.

    Same resolution as ``is_manuscript``, but returning the values rather than
    the boolean, so a reviewer can be *told* the doctype and language instead
    of inferring them from the path.
    """
    return _load_resolver().resolve_axes(path)


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
    parser.add_argument(
        "--axes",
        action="store_true",
        help="instead of the routing verdict, print one "
        "'<path> doctype=<v> lang=<v>' line per file — what a reviewer must be "
        "told so it reads the declared rulebooks rather than guessing them",
    )
    args = parser.parse_args()
    missing = [f for f in args.files if not Path(f).exists()]
    if missing:
        parser.error(
            f"path(s) not found from cwd {Path.cwd()}: {', '.join(missing)} — "
            "anchor the cwd in the checkout that holds the diff; answering "
            "'code' here would be a plausible, wrong verdict"
        )
    if args.axes:
        for path in args.files:
            axes = axes_for(path)
            # An unresolved axis prints "-", never an empty field: a blank
            # reads the same as "not asked", and a reviewer told nothing is
            # exactly the reviewer that guesses.
            print(
                f"{path} doctype={axes.get('doctype', '-')} "
                f"lang={axes.get('lang', '-')}"
            )
        return 0
    print("prose" if diff_is_prose(args.files) else "code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
