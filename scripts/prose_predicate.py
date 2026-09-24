#!/usr/bin/env python3
"""Shared prose/code routing predicate for the review skills (ticket 0550).

A changed file is a *manuscript* iff the axis resolver yields a ``doctype``
for it — from the project manifest (``<repo>/.claude/rules-map.toml``) or,
when no manifest maps it, from the ``\\documentclass`` sniff. Format alone is
NOT the discriminant: process prose (conception notes, ``.erg`` tickets)
resolves to no doctype and stays on the code panel — the 2026-08-17 audit
measured that the code lenses served exactly those diffs correctly.

This module is the single home of the axis resolver (format, doctype, lang,
prose; rules/README.md § Axis model). It used to be loaded from the per-edit
rule-injection hook, deleted by ticket 0976; keep one copy only (ticket 0531
documents what a diverging re-extraction costs).

Project manifest (optional): ``<repo>/.claude/rules-map.toml`` ::

    default_lang = "fr"
    [[map]]
    glob = "slides/manuscript/**/*.tex"
    doctype = "techreport"
    lang = "fr"

The first ``[[map]]`` entry whose glob matches wins; a manifest doctype
overrides the ``\\documentclass`` sniff.

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
import re
import tomllib
from pathlib import Path

# Extension -> format axis value. Project-agnostic by design: keyed on the
# filename suffix, never on a directory like src/ or scripts/.
EXT_FORMAT = {
    ".py": "python",
    ".sh": "bash",
    ".tex": "tex",
    ".qmd": "qmd",
    ".md": "md",
    ".txt": "txt",
}
PROSE_FORMATS = {"tex", "qmd", "md", "txt"}

# \documentclass{X} -> doctype axis value.
DOCUMENTCLASS_DOCTYPE = {
    "report": "techreport",
    "article": "article",
    "beamer": "slides",
    "book": "book",
}
_DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}")


def _glob_to_regex(glob: str) -> str:
    """Translate a path glob to an anchored regex. `**` matches zero or more
    directory segments; `*`/`?` stay within a single segment. Works on 3.11+
    (pathlib.PurePath.full_match is 3.13-only, so we cannot use it)."""
    out = ["(?s:"]
    i, n = 0, len(glob)
    while i < n:
        c = glob[i]
        if glob[i : i + 2] == "**":
            if glob[i + 2 : i + 3] == "/":
                out.append("(?:.*/)?")  # **/  -> zero or more dirs
                i += 3
            else:
                out.append(".*")
                i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    out.append(r")\Z")
    return "".join(out)


def glob_match(rel: str, glob: str) -> bool:
    """Match a repo-relative path against a glob. A slash-less glob also matches
    on the basename alone (so `*.qmd` means "any .qmd anywhere").

    Manifest globs are author-controlled, but guard anyway: collapse runs of 3+
    stars (typos like ``***/``) to ``**`` and reject absurd globs, so a many-``**``
    pattern can't drive catastrophic regex backtracking past the hook timeout."""
    glob = re.sub(r"\*{3,}", "**", glob)
    if len(glob) > 200 or glob.count("*") > 8:
        return False
    pattern = _glob_to_regex(glob)
    if re.match(pattern, rel):
        return True
    return "/" not in glob and re.match(pattern, rel.rsplit("/", 1)[-1]) is not None


def format_for(path: str) -> str | None:
    """Format axis value from the file extension, or None if unstyled."""
    return EXT_FORMAT.get(Path(path).suffix.lower())


def sniff_doctype(path: str, fmt: str | None) -> str | None:
    """Doctype from markup where reliable. Only .tex \\documentclass today."""
    if fmt != "tex":
        return None
    try:
        head = Path(path).read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None
    m = _DOCUMENTCLASS_RE.search(head)
    if not m:
        return None
    cls = m.group(1).strip()
    return DOCUMENTCLASS_DOCTYPE.get(cls, cls)


def find_manifest(path: str) -> Path | None:
    """Walk up from the file for ``.claude/rules-map.toml``."""
    try:
        start = Path(path).resolve().parent
    except OSError:
        return None
    for d in (start, *start.parents):
        candidate = d / ".claude" / "rules-map.toml"
        if candidate.is_file():
            return candidate
    return None


def manifest_axes(path: str, manifest: Path) -> dict[str, str]:
    """Resolve doctype/lang overrides + default_lang from the manifest.

    The first ``[[map]]`` whose glob matches the file (relative to the dir that
    holds ``.claude/``) supplies its doctype/lang. ``default_lang`` is the
    fallback when no entry sets lang.
    """
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    repo_root = manifest.parent.parent  # <repo>/.claude/rules-map.toml -> <repo>
    try:
        rel = str(Path(path).resolve().relative_to(repo_root))
    except ValueError:
        rel = Path(path).name
    out: dict[str, str] = {}
    default_lang = data.get("default_lang")
    if isinstance(default_lang, str):
        out["lang"] = default_lang
    for entry in data.get("map", []):
        if not isinstance(entry, dict):
            continue  # malformed [[map]] entry — skip it, not the whole file
        glob = entry.get("glob")
        if not isinstance(glob, str):
            continue
        if glob_match(rel, glob):
            for axis in ("doctype", "lang"):
                if isinstance(entry.get(axis), str):
                    out[axis] = entry[axis]
            break  # first match wins
    return out


def resolve_axes(path: str) -> dict[str, str]:
    """Compose the axis values for a file.

    format from extension; doctype from markup sniff then manifest override;
    lang from manifest (per-glob, else default_lang); prose implied by format.
    """
    fmt = format_for(path)
    if fmt is None:
        return {}
    axes: dict[str, str] = {"format": fmt}
    if fmt in PROSE_FORMATS:
        axes["prose"] = "_all"

    doctype = sniff_doctype(path, fmt)

    manifest = find_manifest(path)
    overrides = manifest_axes(path, manifest) if manifest else {}
    # Manifest overrides the sniffed doctype; supplies lang (not sniffable).
    doctype = overrides.get("doctype", doctype)
    if doctype:
        axes["doctype"] = doctype
    if overrides.get("lang"):
        axes["lang"] = overrides["lang"]
    return axes


def is_manuscript(path: str) -> bool:
    """True iff the file resolves to a doctype — a rendered deliverable."""
    return "doctype" in resolve_axes(path)


def diff_is_prose(paths: list[str]) -> bool:
    """Any-semantics over a diff's changed files: one manuscript flips it."""
    return any(is_manuscript(p) for p in paths)


def axes_for(path: str) -> dict[str, str]:
    """The file's resolved axes — which house rulebooks apply to it.

    Same resolution as ``is_manuscript``, but returning the values rather than
    the boolean, so a reviewer can be *told* the doctype and language instead
    of inferring them from the path.
    """
    return resolve_axes(path)


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
