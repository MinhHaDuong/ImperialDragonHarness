"""Ticket 0924 — the v8 runtime evidence for Claude Code, Codex and Pi.

Wave 3 of raid-0909 (Vibe was smoked by 0923). One real headless session per
runtime against a disposable clone of this repository exercised the v8
Markdown contract: AGENTS.md loaded and the memory index/theme read before
action, journal search with the runtime's ordinary tools, a public capture
through scripts/memory-capture.sh, no native-profile sync to read the common
memory, and AGENTS.md as the single source. This module pins the shape of
the deliverables — one dated evidence doc per runtime, plus this hunt's own
roar capture — so a regression cannot silently delete the record. As with
the 0923 smoke, it cannot and does not certify the behavioural legs
themselves (design v8 §9: a single sentinel word is not proof of adherence).

The private .age leg stays deferred by author decision F2 (recorded on
0923): captures are public only, and the journal carries no ciphertext.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# One dated evidence doc per runtime, capability-survey shape, per the raid
# annotation of 2026-10-02 (imagine pass) recorded in the ticket body.
RUNTIME_DOCS = {
    "Claude Code": REPO / "docs" / "2026-10-02-memory-v8-runtime-claude-code.md",
    "Codex": REPO / "docs" / "2026-10-02-memory-v8-runtime-codex.md",
    "Pi": REPO / "docs" / "2026-10-02-memory-v8-runtime-pi.md",
}

# This hunt's own roar capture (step 6): the factual episode record of the
# three-runtime verification, written through scripts/memory-capture.sh like
# every other journal entry, clearly marked as smoke evidence.
HUNT_ENTRY = (
    REPO / "memory" / "journal" / "2026" / "2026-10-02-memory-v8-runtimes-verified.md"
)

LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")

# The five per-runtime verification legs of the raid annotation, as the
# evidence docs must section them.
LEGS = (
    "(1) Read-before-action",
    "(2) Journal search",
    "(3) Public capture",
    "(4) Native-profile independence",
    "(5) Single source",
)


def relative_targets(text):
    """Markdown link targets that are repo-relative (scheme-less)."""
    return [
        target
        for target in LINK.findall(text)
        if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target)
    ]


def test_evidence_document_exists_per_runtime():
    for runtime, doc in RUNTIME_DOCS.items():
        assert doc.is_file(), f"missing evidence document for {runtime}: {doc}"


def test_each_document_declares_runtime_and_version():
    # The exact versions this wave actually ran, so a doc that loses them
    # (or drifts into a generic "2.x" claim) fails the pin.
    versions = {
        "Claude Code": "2.1.286",
        "Codex": "0.159.3",
        "Pi": "0.87.1",
    }
    for runtime, doc in RUNTIME_DOCS.items():
        text = doc.read_text(encoding="utf-8")
        assert runtime in text, f"{doc.name}: runtime {runtime!r} not named"
        assert versions[runtime] in text, (
            f"{doc.name}: version {versions[runtime]!r} not recorded"
        )
        # Limits and omissions are reported, not converted into pass marks.
        assert re.search(r"\blimit", text, re.IGNORECASE), (
            f"{doc.name}: observed limits not recorded"
        )


def test_each_document_records_every_leg():
    for doc in RUNTIME_DOCS.values():
        text = doc.read_text(encoding="utf-8")
        for leg in LEGS:
            assert leg in text, f"{doc.name}: lost its {leg!r} section"


def test_each_leg_names_an_independent_evidence_channel():
    # Antipattern: restating what the agent was handed. Every leg section of
    # every evidence doc must carry its own "Evidence channel:" line naming
    # the channel the observation came from — a transcript, an access trace,
    # an observed search hit — never the agent's own restatement of the
    # prompt. Requiring it per section (not just a global count) is what
    # keeps legs (1) and (2), the behavioural legs, pinned.
    for doc in RUNTIME_DOCS.values():
        text = doc.read_text(encoding="utf-8")
        sections = re.split(r"(?m)^## ", text)
        for leg in LEGS:
            matching = [s for s in sections if s.startswith(leg)]
            assert len(matching) == 1, (
                f"{doc.name}: expected exactly one {leg!r} section"
            )
            assert "Evidence channel:" in matching[0], (
                f"{doc.name}: {leg!r} leg does not name its evidence channel"
            )


def test_each_document_records_the_disposable_clone():
    # One real session per runtime, against a disposable clone — the evidence
    # doc must say where the session ran (this wave's scratch root) and that
    # nothing was committed from the clone. Whitespace is normalised first
    # so a phrase wrapped across lines still matches.
    for doc in RUNTIME_DOCS.values():
        text = doc.read_text(encoding="utf-8")
        flat = re.sub(r"\s+", " ", text)
        assert "clone" in flat, f"{doc.name}: disposable clone not recorded"
        assert "/tmp/mem0924/" in flat, (
            f"{doc.name}: the clone's scratch root is not recorded"
        )
        assert re.search(r"[Nn]othing was committed", flat), (
            f"{doc.name}: the no-commit-from-the-clone fact is not recorded"
        )


def test_hunt_capture_exists_and_is_marked():
    text = HUNT_ENTRY.read_text(encoding="utf-8")
    assert "smoke evidence" in text, "hunt capture not marked as smoke evidence"
    for doc in RUNTIME_DOCS.values():
        assert doc.name in text, f"hunt capture does not link {doc.name}"


def test_private_leg_still_deferred_no_ciphertext():
    # Author decision F2 (recorded on 0923): public captures only; the .age
    # mechanism stays unexercised on real material, so the journal stays
    # all-plaintext.
    journal = REPO / "memory" / "journal"
    assert not list(journal.rglob("*.age"))


def test_claude_md_stays_absent_or_a_relative_alias():
    # Exit criterion 2: AGENTS.md is the single source. A CLAUDE.md at the
    # repository root may only be a relative alias of it — never a second,
    # divergent content.
    claude_md = REPO / "CLAUDE.md"
    agents_md = REPO / "AGENTS.md"
    if claude_md.exists():
        if claude_md.is_symlink():
            assert Path(claude_md.resolve()) == Path(agents_md.resolve()), (
                "CLAUDE.md is a symlink but not to AGENTS.md"
            )
        else:
            assert claude_md.read_text(encoding="utf-8") == agents_md.read_text(
                encoding="utf-8"
            ), "CLAUDE.md carries divergent content"


def test_new_documents_link_only_resolving_targets():
    # The pilot's link definition, applied to every new document: anchored
    # links have their anchor stripped, every target must resolve and stay
    # inside the repository.
    for doc in (*RUNTIME_DOCS.values(), HUNT_ENTRY):
        text = doc.read_text(encoding="utf-8")
        for target in relative_targets(text):
            resolved = (doc.parent / target).resolve()
            assert resolved.exists(), f"{doc.name}: dangling link {target}"
            assert resolved == REPO or REPO in resolved.parents, (
                f"{doc.name}: link escapes the repository: {target}"
            )
