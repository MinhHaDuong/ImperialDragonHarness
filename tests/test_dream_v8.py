"""Versioned dreaming prompt and source-preserving editorial workflow (0916).

The pilot dream runs on this repository's own memory. The deliverables this
file pins mechanically, from the ticket's exit criteria:

- ``memory/DREAM.md`` is a versioned consolidation prompt covering pruning,
  merging, refreshing, coherence, the encrypted-entry policy and its three
  failure modes (authentication, malformed ciphertext, re-encryption).
- A dream report under ``memory/dreams/`` cites the prompt revision, the
  runtime/model, and every examined source by git blob revision.
- Two passes do not re-import the same revisions as new, and the pass-1
  correction is re-examined.
- The journal ledger in the report pins the pre-dream journal blobs: the raw
  journal was neither moved nor rewritten by consolidation.
- The governance topic records the private-companion supersession with its
  journal sources preserved; the dream skill no longer offers the private
  companion as a write destination.
"""

import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MEMORY = REPO / "memory"
DREAM_PROMPT = MEMORY / "DREAM.md"
DREAMS = MEMORY / "dreams"
# The pilot dream's own report, pinned by name: a later dated report must not
# hijack these pilot-specific expectations (they describe this dream's
# correction, ledgers and passes).
PILOT_REPORT = DREAMS / "2026-10-02-pilot-first-dream.md"
SKILL = REPO / "skills" / "dream" / "SKILL.md"

# Journal entries on origin/main before the pilot dream. Their blob pins
# prove the dream did not rewrite or move any of them; entries captured
# later are not pinned until a later dream examines them.
PRE_DREAM_JOURNAL = (
    "memory/journal/2026/2026-10-01-memory-helper-retirement.md",
    "memory/journal/2026/2026-10-01-memory-v8-design-and-boundaries.md",
    "memory/journal/2026/2026-10-01-portable-registration-review.md",
    "memory/journal/2026/2026-10-02-memory-v8-merge-under-parallel-housekeeping.md",
    "memory/journal/2026/2026-10-02-memory-v8-pilot-established.md",
    "memory/journal/2026/2026-10-02-reviewer-attribution-design.md",
)

LEDGER = re.compile(r"^- (\S+) blob ([0-9a-f]{40})$")
PASS = re.compile(r"^## Pass (\d)")


def git_blob_sha(path: Path) -> str:
    """Git blob id of a file, computed in-process (no subprocess)."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def report_text() -> str:
    assert PILOT_REPORT.is_file(), (
        f"the pilot dream report is missing: {PILOT_REPORT}"
    )
    return PILOT_REPORT.read_text(encoding="utf-8")


def pass_sections(text: str) -> dict[str, str]:
    """Slices of the report per ``## Pass n`` heading."""
    sections: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        match = PASS.match(line)
        if match:
            current = match.group(1)
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def ledger(section: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2)
        for match in (LEDGER.match(line) for line in section.splitlines())
        if match
    }


def test_dream_prompt_is_versioned_and_complete():
    text = DREAM_PROMPT.read_text(encoding="utf-8")
    assert re.search(r"^Prompt revision: \S+", text, re.MULTILINE), (
        "memory/DREAM.md carries no Prompt revision line"
    )
    for function in ("Pruning", "Merging", "Refreshing"):
        assert function in text, f"prompt lacks {function}"
    assert "100 lines" in text, "prompt lacks the index cap"
    assert "append-only" in text, "prompt lacks the journal invariant"
    assert ".age" in text, "prompt lacks the encrypted-entry policy"
    assert "skipped" in text and "never" in text, (
        "prompt does not define skip-and-count for unavailable keys"
    )
    for failure in ("authentication", "malformed", "re-encrypt"):
        assert failure in text, f"prompt lacks {failure} failure handling"


def test_convention_docs_point_at_the_live_prompt():
    text = (REPO / "docs" / "memory-v8" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "memory/DREAM.md" in text, (
        "the adopting convention does not name the versioned prompt"
    )


def test_dream_skill_reconciles_the_private_companion():
    text = SKILL.read_text(encoding="utf-8")
    assert "private companion" not in text, (
        "the dream skill still offers the private companion as a destination"
    )
    assert ".age" in text, "the dream skill ignores encrypted entries"
    for failure in ("authentication", "malformed", "re-encrypt"):
        assert failure in text, f"the dream skill lacks {failure} handling"


def test_pilot_report_cites_prompt_revision_runtime_and_model():
    text = report_text()
    assert re.search(r"^Prompt revision: \S+", text, re.MULTILINE)
    assert re.search(r"^Runtime: \S.*", text, re.MULTILINE)
    assert re.search(r"^Model: \S.*", text, re.MULTILINE)
    assert "blob " in text, "report cites no source revision"
    assert "Unresolved" in text, "report lists no open questions"
    assert re.search(r"^Encrypted entries skipped: \d+", text, re.MULTILINE)


def test_two_passes_do_not_reimport_and_reexamine_the_correction():
    text = report_text()
    sections = pass_sections(text)
    assert set(sections) >= {"1", "2"}, "report has no two passes"
    first, second = ledger(sections["1"]), ledger(sections["2"])
    assert first, "pass 1 records no revision ledger"
    journal_1 = {p: s for p, s in first.items() if "/journal/" in p}
    journal_2 = {p: s for p, s in second.items() if "/journal/" in p}
    assert journal_2 == journal_1, "pass 2 re-imports journal revisions"
    reimported = {
        path for path in second
        if path not in first or second[path] != first[path]
    }
    # The only fresh revisions pass 2 may see are files pass 1 itself wrote.
    pass1_products = {
        line[len("- writes "):].strip()
        for line in sections["1"].splitlines()
        if line.startswith("- writes ")
    }
    assert reimported <= pass1_products, (
        f"pass 2 imports revisions pass 1 never produced: {reimported}"
    )
    assert "Imported as new: none" in sections["2"], (
        "pass 2 does not state that it imported nothing new"
    )
    assert "re-examin" in sections["2"], (
        "pass 2 does not record the correction re-examination"
    )


def test_report_journal_ledger_pins_the_untouched_journal():
    text = report_text()
    sections = pass_sections(text)
    first = ledger(sections["1"])
    for rel in PRE_DREAM_JOURNAL:
        assert rel in first, f"report ledger omits {rel}"
        assert first[rel] == git_blob_sha(REPO / rel), (
            f"{rel}: ledger blob does not match the file — journal rewritten?"
        )
    for path in first:
        assert (REPO / path).is_file(), (
            f"ledger names a missing file: {path}"
        )


def test_governance_topic_records_supersession_with_sources():
    topic = MEMORY / "topics" / "memory-v8-governance.md"
    text = topic.read_text(encoding="utf-8")
    assert "declared private companion" not in text, (
        "the superseded private-companion claim still reads as current"
    )
    assert "superseded" in text, "the topic does not record the supersession"
    assert ".age" in text or "encrypted" in text, (
        "the topic does not state the encrypted-in-repo policy"
    )
    assert (
        "journal/2026/2026-10-02-memory-v8-pilot-established.md" in text
    ), "the corrected claim lost its journal source"
