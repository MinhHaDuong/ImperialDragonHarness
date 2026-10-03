"""
Ticket 1018 wave A: the Zotero backend is scripts/zotero.py, and no live
file cites the retired backend path.

The backend rename landed first (wave A); the skill consolidation (wave B)
follows. This ratchet is the mechanical guard for the rename sweep: any NEW
citation of the retired script in a live surface fails, and the surviving
wave B naming sites are pinned line-by-line as provenance until wave B
removes them.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()

# The retired script, in any of its live spellings — bare basename run lines
# (`zotero-import.py audit ...`), full-path citations, and $IDH_ROOT forms.
# The sweep below covers this test's own directory, so the pattern is built by
# concatenation: this file's source never contains the contiguous literal.
RETIRED = re.compile(r"zotero-import" + r"\.py")

# Live surfaces the sweep covers; STATE.md is a live pointer file.
SURFACES = ("skills", "rules", "docs", "tests", "scripts")

# Records, not live pointers (mirrors the ticket's do-not-touch list): ticket
# history and project memory are archives; audit records and the reviewer
# benchmark board record past runs under the name they ran under.
EXCLUDED_PARTS = ("tickets", "projects")
EXCLUDED_NAMES = ("benchmark-board.yml",)
AUDIT_RECORD = re.compile(r"audit", re.IGNORECASE)

# The ten backend verbs (ticket 1018: subcommand names are the verbs).
VERBS = {
    "probe",
    "match",
    "dedup-report",
    "sync-index",
    "audit",
    "reconcile",
    "attach",
    "write",
    "inject",
    "enrich",
}

# Provenance: path relative to ROOT -> substrings each surviving line must
# carry. Keyed by full relative path (not basename) so a same-named file in a
# subdirectory cannot inherit another file's exemption. A match in any other
# path, or a surviving line that no longer carries one of its substrings, is
# a new live reference: red. Wave B (skill consolidation) removes all three.
PROVENANCE = {
    # Wave B rewrites the SKILL.md body as the verb router; until then its
    # pointer at the helper documentation still names the retired script.
    "skills/zotero-import/SKILL.md": (
        "lookup and write",
    ),
    # Wave B absorbs index-source (probe-url.py with it); the DOI-regex
    # mirror comment keeps naming its sibling until then.
    "skills/index-source/scripts/probe-url.py": (
        "mirrors",
    ),
    # Wave B naming site (ticket Action 4): the design doc's status sentence
    # names the backend it consolidates ("is ticketed"), and its Upload PDF
    # row is a historical record of the MR #760 run line.
    "docs/zotero-integration.md": (
        "is ticketed",
        "MR #760",
    ),
}


def _surface_files():
    for surface in SURFACES:
        for path in sorted((ROOT / surface).rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            yield path
    yield ROOT / "STATE.md"


def _is_excluded(path):
    rel_parts = path.relative_to(ROOT).parts
    if any(part in EXCLUDED_PARTS for part in rel_parts):
        return True
    if path.name in EXCLUDED_NAMES:
        return True
    return bool(AUDIT_RECORD.search(path.name))


def _retired_matches():
    for path in _surface_files():
        if path.resolve() == SELF or _is_excluded(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if RETIRED.search(line):
                yield path.relative_to(ROOT).as_posix(), lineno, line


def _is_exempt(name, line):
    return name in PROVENANCE and any(sub in line for sub in PROVENANCE[name])


@pytest.mark.adherence
def test_no_live_citations_of_retired_backend():
    offenders = []
    for name, lineno, line in _retired_matches():
        if _is_exempt(name, line):
            continue
        offenders.append(f"{name}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Live citation(s) of the retired Zotero backend (ticket 1018):\n"
        + "\n".join(offenders)
    )


@pytest.mark.adherence
def test_zotero_backend_answers_all_ten_verbs():
    backend = ROOT / "scripts" / "zotero.py"
    assert backend.is_file(), (
        "scripts/zotero.py is missing (ticket 1018 wave A rename)"
    )
    text = backend.read_text(encoding="utf-8")
    parsers = set(re.findall(r"add_parser\(\s*[\"']([^\"']+)[\"']", text))
    missing = VERBS - parsers
    assert not missing, (
        f"scripts/zotero.py is missing subcommand(s): {sorted(missing)}"
    )


@pytest.mark.adherence
def test_provenance_exemptions_still_live():
    # A stale exemption (wave B removed the site but left the pin here) is
    # itself red: the ratchet must tighten, not accumulate carve-outs.
    live = {name: False for name in PROVENANCE}
    for name, _lineno, line in _retired_matches():
        if _is_exempt(name, line):
            live[name] = True
    dead = sorted(name for name, ok in live.items() if not ok)
    assert not dead, (
        f"provenance exemption(s) with no surviving citation (remove them): {dead}"
    )
