"""
Ticket 1018: the Zotero backend is scripts/zotero.py and the skill surface is
one `zotero` skill with verbs; no live file cites the retired names.

Two ratchets, one per wave. Wave A renamed the backend
(zotero-import.py -> zotero.py): any NEW citation of the retired script in a
live surface fails. Wave B consolidated the skills (zotero-import +
index-source -> zotero): the consolidated router must exist, the retired
skill directories must be gone, and no live file may cite the retired skill
names in a citation form (a skills/ path, a backticked /command invocation,
or a backticked bare name).

Bare unbackticked prose is out of scope for the skill-name sweep: the
historical cache segment ~/.cache/zotero-import/ deliberately keeps the old
name (ticket 1018), and record files quote past runs in plain prose.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()

sys.path.insert(0, str(ROOT / "scripts"))
import skill_frontmatter as sf  # noqa: E402

# The retired script, in any of its live spellings — bare basename run lines
# (`zotero-import.py audit ...`), full-path citations, and $IDH_ROOT forms.
# The sweep below covers this test's own directory, so the pattern is built by
# concatenation: this file's source never contains the contiguous literal.
RETIRED = re.compile(r"zotero-import" + r"\.py")

# The retired skill names, in the forms a citation takes: a skills/ path
# (`skills/index-source/scripts/...`), a backticked slash invocation
# (`/zotero-import`), or a backticked bare name (`zotero-import`). Built by
# concatenation for the same self-concealment reason as RETIRED.
SKILL_NAME = "(?:zotero-import|index-source)"
RETIRED_SKILL = re.compile(
    r"skills/" + SKILL_NAME + r"\b"
    r"|`/" + SKILL_NAME + "`"
    r"|`" + SKILL_NAME + "`"
)

# Live surfaces the sweeps cover; STATE.md and the catalog README are live
# pointer files.
SURFACES = ("skills", "rules", "docs", "tests", "scripts")

# Records, not live pointers (mirrors the ticket's do-not-touch list): ticket
# history and project memory are archives; audit records and the reviewer
# benchmark board record past runs under the name they ran under.
EXCLUDED_PARTS = ("tickets", "projects")
# Audit records are excluded by EXACT name, not an "audit" substring —
# a substring blind-spots live files (review of PR #1179: audition.md,
# mammoth-audit.py would slip). New record files must be exempted
# explicitly: fail-safe direction, records never silently skip the sweep.
EXCLUDED_NAMES = (
    "benchmark-board.yml",
    "2026-09-24-rules-coherence-audit.md",
    "audit-0252-worktree-ownership-2026-07-12.md",
    "trace-compact-audit-2026-06.md",
)

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

# The verb-router surface (ticket 1018 wave B): what a user types after the
# skill name. `attach` is declared, created on first need (YAGNI).
ROUTER_VERBS = ("import", "enrich", "audit", "reconcile", "dedup-report", "attach")

# The consolidated skill.
ZOTERO_SKILL = ROOT / "skills" / "zotero" / "SKILL.md"
RETIRED_SKILL_DIRS = ("skills/zotero-import", "skills/index-source")

# Provenance: path relative to ROOT -> substrings each surviving line must
# carry. Wave B cleared every pinned site (the SKILL.md router rewrite, the
# probe-url.py mirror comment, the design doc's status sentence), so the
# exemption list is empty: both sweeps are now unconditional. Re-pin a site
# here — with its justifying substring — only for a deliberate transition
# window, and remove the pin when the window closes.
PROVENANCE = {}


def _surface_files():
    for surface in SURFACES:
        for path in sorted((ROOT / surface).rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            yield path
    yield ROOT / "STATE.md"
    yield ROOT / "README.md"


def _is_excluded(path):
    rel_parts = path.relative_to(ROOT).parts
    if any(part in EXCLUDED_PARTS for part in rel_parts):
        return True
    if path.name in EXCLUDED_NAMES:
        return True
    return False


def _matches(pattern):
    for path in _surface_files():
        if path.resolve() == SELF or _is_excluded(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                yield path.relative_to(ROOT).as_posix(), lineno, line


def _is_exempt(name, line):
    return name in PROVENANCE and any(sub in line for sub in PROVENANCE[name])


@pytest.mark.adherence
def test_no_live_citations_of_retired_backend():
    offenders = []
    for name, lineno, line in _matches(RETIRED):
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
    # A stale exemption (a removed site left pinned here) is itself red: the
    # ratchet must tighten, not accumulate carve-outs.
    live = {name: False for name in PROVENANCE}
    for name, _lineno, line in _matches(RETIRED):
        if _is_exempt(name, line):
            live[name] = True
    dead = sorted(name for name, ok in live.items() if not ok)
    assert not dead, (
        f"provenance exemption(s) with no surviving citation (remove them): {dead}"
    )


# --- Wave B: the consolidated skill surface ---


@pytest.mark.adherence
def test_consolidated_skill_is_named_zotero():
    assert ZOTERO_SKILL.is_file(), (
        "skills/zotero/SKILL.md is missing (ticket 1018 wave B consolidation)"
    )
    assert sf.load(ZOTERO_SKILL)["name"] == "zotero", (
        "skills/zotero/SKILL.md frontmatter must declare name: zotero"
    )


@pytest.mark.adherence
def test_retired_skills_are_gone():
    for retired in RETIRED_SKILL_DIRS:
        skill = ROOT / retired / "SKILL.md"
        assert not skill.exists(), (
            f"{retired} still ships a SKILL.md — the catalog would list a "
            "retired skill (ticket 1018 wave B)"
        )


@pytest.mark.adherence
def test_router_declares_the_verb_surface():
    assert ZOTERO_SKILL.is_file(), "skills/zotero/SKILL.md is missing"
    text = ZOTERO_SKILL.read_text(encoding="utf-8")
    missing = [
        verb for verb in ROUTER_VERBS
        if not re.search(rf"\|\s*`?{re.escape(verb)}`?\s*\|", text)
    ]
    assert not missing, (
        f"the verb router does not declare verb(s): {missing} — the surface "
        "must mirror the backend subcommands (ticket 1018)"
    )


@pytest.mark.adherence
def test_no_live_citations_of_retired_skill_names():
    offenders = [f"{name}:{lineno}: {line.strip()}"
                 for name, lineno, line in _matches(RETIRED_SKILL)]
    assert not offenders, (
        "Live citation(s) of the retired Zotero skill names (ticket 1018 "
        "wave B — consolidated into the `zotero` skill):\n"
        + "\n".join(offenders)
    )
