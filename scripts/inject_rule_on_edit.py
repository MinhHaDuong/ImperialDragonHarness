#!/usr/bin/env python3
"""PreToolUse(Edit|Write) hook: inject matching GLOBAL rule bodies on the first
edit of a file along each axis, once per session.

The rulebook in ``rules/`` is shared across every project. The session-start
hook injects only the rules INDEX (pointers); bodies are read on demand. This
hook tightens that for files with style rules: it resolves the edited file along
four orthogonal axes and injects the body of every matching global rule that
exists, then stays silent for the rest of the session (deduped per
``session_id`` + rule file).

Axes (composed per file):
  format  — from the filename extension (project-agnostic). py/sh/tex/qmd/md/txt.
  doctype — sniffed from markup where reliable (\\documentclass for .tex);
            overridable by a project manifest. e.g. techreport/article/slides.
  lang    — not mechanically detectable; from the project manifest, else the
            manifest's default_lang. e.g. fr/en.
  prose   — implied for prose formats (tex/qmd/md/txt); injects prose/_all.md
            (LLMism guards, Elements of Style) regardless of doctype/lang.

Rule files live by convention ``rules/<axis>/<value>.md`` (e.g.
``rules/format/python.md``, ``rules/doctype/techreport.md``, ``rules/lang/fr.md``,
``rules/prose/_all.md``). Legacy flat code rules (``rules/coding-python.md``,
``rules/coding-bash.md``) are reached via a fallback alias so no rename is
needed; missing files are silently skipped, so content grows by adding files.

Project manifest (optional): ``<repo>/.claude/rules-map.toml`` ::

    default_lang = "fr"
    [[map]]
    glob = "slides/manuscript/**/*.tex"
    doctype = "techreport"
    lang = "fr"

Output: JSON on stdout with ``hookSpecificOutput.additionalContext`` (exit 0).
Claude surfaces it in a system reminder before the edit runs. Framing is
declarative (a fact about the file), never imperative, per the harness
hook-output convention. The hook is advisory: any error exits 0 silently so it
can never block an edit.
"""

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path

from path_utils import contained

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

# Keep injected context under the platform's 10,000-char additionalContext cap.
MAX_CONTEXT = 9500

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
    """Walk up from the edited file for ``.claude/rules-map.toml``."""
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
    """Resolve doctype/lang overrides + default_lang from the project manifest.

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
    """Compose all axis values for the edited file.

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


def candidate_rule_files(axes: dict[str, str], rules_dir: Path) -> list[Path]:
    """Existing rule files for the resolved axes, in injection order.

    Convention: ``rules/<axis>/<value>.md``. Format has a legacy-alias fallback
    (``rules/coding-<value>.md``) so the flat code rules need no rename.

    An axis value is not trusted: ``doctype`` is sniffed from the edited file's
    ``\\documentclass{...}`` (which accepts ``/`` and ``..``), and ``doctype``/
    ``lang`` can come from a project ``rules-map.toml``. A value like
    ``../../../etc/whatever`` would otherwise resolve outside the rulebook and
    inject an arbitrary ``.md`` body into the model context. Every candidate is
    therefore resolved through ``contained()`` and dropped if it escapes
    ``rules_dir``.
    """
    files: list[Path] = []
    for axis in ("format", "doctype", "lang", "prose"):
        value = axes.get(axis)
        if not value:
            continue
        rels = [f"{axis}/{value}.md"]
        if axis == "format":
            rels.append(f"coding-{value}.md")
        for rel in rels:
            c = contained(rules_dir, rel)
            if c is not None and c.is_file():
                files.append(c)
                break
    return files


def marker_path(session_id: str, rule: Path) -> Path:
    base = Path(os.environ.get("TMPDIR", "/tmp")) / "claude-rule-inject"
    # session_id is untrusted stdin — sanitize so it cannot escape the dir.
    sid = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "nosession")[:64]
    return base / f"{sid}.{rule.parent.name}.{rule.name}"


def build_context(path: str, axes: dict[str, str], files: list[Path]) -> str:
    fmt = axes.get("format", "")
    desc = ", ".join(f"{k}={v}" for k, v in axes.items())
    parts = [
        f"You are editing a {fmt} file ({path}). Its global style rules "
        f"({desc}) apply to such files in this session. They are reproduced "
        f"once below for reference:"
    ]
    for f in files:
        parts.append(f"\n----- {f.parent.name}/{f.name} -----\n{f.read_text(encoding='utf-8').rstrip()}")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rules-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "rules",
        help="Directory holding the global rule tree (default: ../rules).",
    )
    args = parser.parse_args()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # advisory: never block on bad input

    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        return 0

    axes = resolve_axes(file_path)
    files = candidate_rule_files(axes, args.rules_dir)
    if not files:
        return 0

    session_id = payload.get("session_id") or ""
    fresh: list[Path] = []
    for f in files:
        marker = marker_path(session_id, f)
        if marker.exists():
            continue  # already injected this rule this session
        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch()
        except OSError:
            pass  # dedup best-effort; still inject
        fresh.append(f)
    if not fresh:
        return 0

    context = build_context(file_path, axes, fresh)
    if len(context) > MAX_CONTEXT:
        context = context[:MAX_CONTEXT] + "\n\n[... truncated at the additionalContext size limit ...]"
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}},
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    # Advisory hook: never block the edit. Catch SystemExit too (argparse on a
    # bad invocation raises it) so the hook can never exit non-zero, which a
    # PreToolUse hook signals as "block the tool".
    try:
        main()
    except (Exception, SystemExit):
        pass
    sys.exit(0)
