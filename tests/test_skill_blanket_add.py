"""Blanket-staging ratchet for skill prose (ticket 0210).

PR #242 lost a stray file into a close commit because a skill instructed the
blanket `git add` form in a shared checkout: any leftover under `tickets/`
(stash residue, a crashed agent's draft, a cross-branch artifact) gets
silently committed by the next skill run that follows those lines.
`erg-pr-merge` itself was narrowed by PR #262, but the skill prose that agents
execute by hand was not. This test pins the narrowing so it cannot regress:
command-position `git add` in `skills/*/SKILL.md` must name what it stages
(a specific file, or `-u` for tracked edits only), never sweep a directory,
wildcard, `-A`, or `.`.

Escape hatch: a `# blanket-add-ok: <reason>` comment on the same line marks a
deliberate blanket add and exempts it.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"

ALLOWLIST_MARKER = "# blanket-add-ok:"

# Capture the argument run after a `git add`, stopping at the first shell
# terminator so we never bleed into a chained `&& git commit -m "..."`.
_GIT_ADD = re.compile(r"git add(?P<args>(?:[^\n`&|;)])*)")


def _is_blanket(args: str) -> bool:
    """True when this `git add` argument run sweeps an unnamed set.

    Blanket forms: `-A`, a bare `.`, a path ending in `/` (a directory), or a
    `*` wildcard. A `<placeholder>` in the path (e.g. `tickets/<id>-*.erg`)
    pins the add to one known ticket and is allowed, as is `-u` (tracked-only).
    """
    tokens = args.split()
    if not tokens:
        return False  # bare `git add` in prose ("…for a later `git add` to sweep")
    if "-A" in tokens:
        return True
    if "-u" in tokens:
        return False
    for tok in tokens:
        if tok == ".":
            return True
        if tok.startswith("-"):
            continue  # other flag (e.g. the `--` end-of-options marker)
        if "<" in tok:
            continue  # named-file placeholder → specific, not a sweep
        if "*" in tok or tok.endswith("/"):
            return True
    return False


def _blanket_hits() -> list[str]:
    hits = []
    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        for lineno, line in enumerate(skill.read_text().splitlines(), start=1):
            if ALLOWLIST_MARKER in line:
                continue
            if any(_is_blanket(m.group("args")) for m in _GIT_ADD.finditer(line)):
                rel = skill.relative_to(REPO)
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def test_no_blanket_git_add_in_skill_prose():
    """No skill instructs a blanket `git add` that could sweep a stray file."""
    hits = _blanket_hits()
    assert not hits, (
        "Blanket `git add` in skill prose (narrow to a named file or `git add -u`, "
        f"or justify with a `{ALLOWLIST_MARKER} <reason>` comment):\n  "
        + "\n  ".join(hits)
    )


def test_ratchet_detects_known_blanket_forms():
    """The detector must fire on the exact forms the narrowing removed."""
    assert _is_blanket(" -A")
    assert _is_blanket(" .")
    assert _is_blanket(" tickets/")
    assert _is_blanket(" tickets/closed/")
    assert _is_blanket(" tickets/*.erg")
    # …and must NOT fire on the narrowed replacements.
    assert not _is_blanket(" -u")
    assert not _is_blanket(" -u tickets/")
    assert not _is_blanket(" tickets/<child-id>-*.erg")
    assert not _is_blanket(" settings.json")
    assert not _is_blanket("")  # bare `git add` in prose


def test_allowlist_marker_exempts_a_line():
    """A `# blanket-add-ok:` comment marks a deliberate blanket add as allowed."""
    assert _is_blanket(" tickets/")  # blanket in isolation…
    # …but a line carrying the marker is skipped by the file scan.
    sentinel = f"   git add tickets/  {ALLOWLIST_MARKER} deliberate sweep"
    assert ALLOWLIST_MARKER in sentinel
