#!/usr/bin/env python3
"""Project-specific domain-knowledge hints: catalog at session start, body on demand.

A project may hold knowledge a general agent does not have and cannot search
for — a canon, a controlled vocabulary, a map of a field. That material is
*project-specific*, which is what makes it different from everything else this
harness injects: `rules/` keeps its text global and lets a project supply only
mappings, deliberately, so the rulebook stays shared. Here the ownership
inverts. The body lives in the repo; only the mechanism is shared.

Three properties, each paid for by a defect seen in practice.

**The pointer is injected, never the payload.** A field map measured 14.5k
tokens against a 1.7k roster and a 157-token pointer; only the pointer can
afford to be resident. Cost then scales with use rather than with the size of
what the project happens to know.

**The caveat travels with the pointer.** A caveat kept in a separate document is
one nobody opens. Measured 2026-08-19: what a caveat buys is *not* refusal of
bad inferences — a model with no access at all already refuses those, and argues
them well. What it buys is provenance discipline: an agent holding the artifact
flagged, unprompted, which of its answers rested on the artifact rather than on
a page it had opened. That distinction is what disappears without it.

**Discovery cannot depend on vocabulary.** Term triggers need the user to say
"Cournot"; asked about "this paragraph on duopoly", nothing fires, and an agent
cannot grep for words it does not yet have. So a one-line catalog entry is
resident, and the term channel only sharpens it.

**Write the summary context-free.** It is read by an agent that does not yet
know the field, so it must name the domain and the object before any shorthand
an insider would use. "196 entries of Faccarello & Kurz 2016" identifies nothing
unless you already know who they are; "History of economic thought: the 196
entries of the Elgar Handbook on the History of Economic Analysis" routes
someone who does not. A summary that presumes membership in the field cannot do
the one job it has, which is to reach a reader from outside it.

Manifest: ``<repo>/.knowledge.toml`` — deliberately not named for any vendor,
since the repo outlives the tool.

    [[hint]]
    id      = "het-field-map"
    summary = "196 entries of Faccarello & Kurz 2016, folios, 1613 cross-references"
    pointer = "conception/handbook-canon.md"
    full    = "conception/handbook-map.md"     # optional, named not read
    caveat  = "records the 2016 classification, not source content"
    terms   = ["Cournot", "Handbook"]          # optional
    paths   = ["article-het/**"]               # optional, reserved for the edit channel

Absent manifest, absent file, malformed TOML: silent no-op. A hint whose
``pointer`` does not resolve is dropped rather than advertised, so the catalog
never names a file that is not there.
"""

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path

from path_utils import contained

MANIFEST = ".knowledge.toml"
MAX_SUMMARY = 200
MAX_ID = 64
MAX_HINTS = 24
TRUNCATED = "(cap)"
MAX_CAVEAT = 600


def find_manifest(start: Path) -> Path | None:
    """Walk up from `start` for the project manifest."""
    try:
        here = start.resolve()
    except OSError:
        return None
    for d in (here, *here.parents):
        candidate = d / MANIFEST
        if candidate.is_file():
            return candidate
    return None


def _one_line(text: str, cap: int) -> str:
    """Collapse to a single line and cap.

    The catalog budget is stated per *line*; a summary containing newlines
    renders as several, and the cap alone does not prevent it.
    """
    return re.sub(r"\s+", " ", text).strip()[:cap]


def _str_list(value: object) -> list[str]:
    """Non-blank strings from a TOML array, or nothing.

    A scalar `terms = "Cournot"` is iterable: taken as a list it yields one
    entry per character, and a lone "o" then fires the hint on almost any
    prompt. Only a real array counts.
    """
    if not isinstance(value, list):
        return []
    return [v for v in value if isinstance(v, str) and v.strip()]


def load_hints(manifest: Path) -> list[dict]:
    """Parsed hints, each with a resolvable contained pointer. Never raises."""
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # ValueError covers TOMLDecodeError and UnicodeDecodeError alike: a
        # manifest saved in Latin-1 is an ordinary editor accident, and it must
        # not be able to traceback on every prompt of the session.
        return []
    if not isinstance(data, dict):
        return []
    root = manifest.parent
    out = []
    for raw in data.get("hint", []):
        if not isinstance(raw, dict):
            continue
        hid, summary = raw.get("id"), raw.get("summary")
        pointer = raw.get("pointer")
        if not (isinstance(hid, str) and isinstance(summary, str)
                and isinstance(pointer, str)):
            continue
        # A catalog that advertises a missing file is worse than a silent one:
        # the agent spends a turn discovering the pointer is a dead end.
        # ...and a pointer that escapes the repo is worse than either.
        target = contained(root, pointer)
        if target is None or not target.is_file():
            continue
        full = raw.get("full")
        if isinstance(full, str):
            full_t = contained(root, full)
            full = full if full_t is not None and full_t.is_file() else None
        else:
            full = None
        caveat = raw.get("caveat")
        out.append({
            # Capped like `summary`: `id` is resident in the catalog line, so an
            # unbounded one defeats the very budget MAX_SUMMARY exists to hold.
            "id": _one_line(hid, MAX_ID),
            "summary": _one_line(summary, MAX_SUMMARY),
            "pointer": pointer,
            "full": full,
            "caveat": _one_line(caveat, MAX_CAVEAT) if isinstance(caveat, str) else None,
            # An empty term compiles to `(?<!\w)(?!\w)`, which matches beside
            # almost any punctuation -- one stray "" turns "fires on a declared
            # term" into "fires on the first punctuated prompt of the session".
            "terms": _str_list(raw.get("terms")),
            "paths": _str_list(raw.get("paths")),
        })
        if len(out) >= MAX_HINTS:
            # Per-field caps bound each line; only this bounds the total. The
            # catalog is resident at every session start, so an unbounded count
            # defeats the budget as surely as an unbounded field.
            dropped = len(data.get("hint", [])) - MAX_HINTS
            if dropped > 0:
                # Named, not swallowed: a cap that hides what it dropped reads
                # as "this is everything" when it is not.
                out.append({"id": TRUNCATED, "summary": f"{dropped} further "
                            "hints declared but not shown (cap reached)",
                            "pointer": None, "full": None, "caveat": None,
                            "terms": [], "paths": []})
            break
    return out


def render_catalog(hints: list[dict]) -> str:
    """One line per hint. Resident at session start, so it stays terse."""
    if not hints:
        return ""
    lines = [
        "Project domain knowledge is recorded in the files below. They are "
        "pointers, not bodies, and each carries its own caveat in its header:"
    ]
    for h in hints:
        tail = f" → `{h['pointer']}`" if h["pointer"] else ""
        lines.append(f"- {h['id']} — {h['summary']}{tail}")
    return "\n".join(lines)


def match_terms(hints: list[dict], text: str) -> list[dict]:
    """Hints whose declared terms appear in `text`, whole-word, case-folded."""
    hay = text.casefold()
    hit = []
    for h in hints:
        for term in h["terms"]:
            if re.search(rf"(?<!\w){re.escape(term.casefold())}(?!\w)", hay):
                hit.append(h)
                break
    return hit


def render_hint(h: dict) -> str:
    parts = [
        f"Project domain knowledge — {h['id']}: {h['summary']}",
        f"This project records that knowledge in `{h['pointer']}`.",
    ]
    if h["full"]:
        parts.append(f"Fuller material is in `{h['full']}`.")
    if h["caveat"]:
        parts.append(f"It carries this caveat: {h['caveat']}")
    return " ".join(parts)


def marker_path(session_id: str, hid: str) -> Path:
    base = Path(os.environ.get("TMPDIR", "/tmp")) / "claude-knowledge-hints"
    # session_id and id are untrusted input — sanitize so neither escapes the dir.
    sid = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "nosession")[:64]
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", hid)[:64]
    return base / f"{sid}.{safe}"


def cmd_catalog(args: argparse.Namespace) -> int:
    manifest = find_manifest(Path(args.cwd))
    if manifest is None:
        return 0
    text = render_catalog(load_hints(manifest))
    if text:
        print(text)
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    """UserPromptSubmit channel: name the hint once per session, on a term hit."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0  # `[]`, `42`, `null` all parse, then crash on .get
    prompt = payload.get("prompt") or ""
    session_id = payload.get("session_id") or ""
    cwd = payload.get("cwd") or args.cwd

    manifest = find_manifest(Path(cwd))
    if manifest is None:
        return 0
    fresh = []
    for h in match_terms(load_hints(manifest), prompt):
        marker = marker_path(session_id, h["id"])
        if marker.exists():
            continue
        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch()
        except OSError:
            pass  # cannot dedup; better to repeat than to stay silent
        fresh.append(h)
    if fresh:
        print("\n".join(render_hint(h) for h in fresh))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cwd", default=os.getcwd(),
                    help="directory to resolve the project manifest from")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("catalog", help="one line per hint, for session start")
    sub.add_parser("prompt", help="UserPromptSubmit hook; reads JSON on stdin")
    args = ap.parse_args()
    return {"catalog": cmd_catalog, "prompt": cmd_prompt}[args.cmd](args)


if __name__ == "__main__":
    # Advisory hook, and the prompt channel has no shell wrapper to absorb a
    # failure: a traceback here would surface on every prompt of the session,
    # which is worse than the hint never appearing. Same contract as the
    # sibling inject_rule_on_edit.py.
    try:
        main()
    except (Exception, SystemExit):
        pass
    sys.exit(0)
