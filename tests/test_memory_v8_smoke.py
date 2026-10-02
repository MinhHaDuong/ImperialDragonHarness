"""Ticket 0923 — the v8 runtime smoke deliverables stay in place.

The smoke ran 2026-10-02 in this runtime (Vibe CLI, already justified by
the pilot declaration; no runtime selection was re-run). Its deliverables
are one evidence document recording the five legs, one deliberate public
journal capture through scripts/memory-capture.sh (clearly marked as
smoke evidence), the private-leg deferral recorded honestly, and the
contradictory-note and negative-control limits. This module pins their
shape so a regression cannot silently delete the smoke's record — it
does not and cannot certify the behavioural legs themselves
(design v8 §9: a single sentinel word is not proof of adherence).
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "docs" / "2026-10-02-memory-v8-runtime-smoke.md"
ENTRY = REPO / "memory" / "journal" / "2026" / "2026-10-02-memory-v8-smoke.md"

# One dated section per leg of the raid annotation (2026-10-02).
LEGS = (
    "(a) Read-before-action",
    "(b) Public capture",
    "(c) Contradictory native note",
    "(d) Arbitrary-path clone",
    "(e) Miswired-delivery negative control",
)


def test_evidence_document_records_every_leg():
    text = EVIDENCE.read_text(encoding="utf-8")
    for leg in LEGS:
        assert leg in text, f"evidence document lost its {leg!r} section"
    # The runtime is declared, not re-selected (raid annotation premise).
    assert "Vibe" in text


def test_evidence_document_records_the_private_leg_deferral():
    text = EVIDENCE.read_text(encoding="utf-8")
    # Author decision F2: public capture only, the .age leg deferred
    # until real uncleared material exists, limit recorded honestly.
    assert "deferred" in text
    assert ".age" in text


def test_deliberate_public_capture_exists_and_is_marked():
    text = ENTRY.read_text(encoding="utf-8")
    # The capture is the smoke's own evidence entry, clearly marked as
    # such (antipattern: artificial journal entries).
    assert "smoke evidence" in text
    # The evidence document links back from the entry.
    assert "2026-10-02-memory-v8-runtime-smoke.md" in text


def test_no_ciphertext_entry_from_the_deferred_leg():
    # The deferred private leg must not leave an unexercised .age stub:
    # the smoke added none, so the journal stays all-plaintext.
    journal = REPO / "memory" / "journal"
    assert not list(journal.rglob("*.age"))


def test_evidence_document_links_only_resolving_targets():
    text = EVIDENCE.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)#\s]+)\)", text):
        if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target):
            continue
        assert (EVIDENCE.parent / target).exists(), f"dangling link: {target}"
