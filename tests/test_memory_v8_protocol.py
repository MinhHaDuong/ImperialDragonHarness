"""Ticket 0918 STEP A — the v8 evaluation protocol is predeclared.

Design v8 §9 (docs/2026-09-10-dragon-memory-design.md) and the Astra
clarification require the evaluation protocol to be committed before the
first acceptance trial, with earlier exploratory smokes excluded by commit
reference. This module pins the protocol document's shape so the margins
cannot silently change after a successful example — it does not and cannot
certify the trials themselves (STEP B, same ticket).
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "docs" / "memory-v8" / "evaluation-protocol.md"

LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")

# The ten trials of the design §9 acceptance table, by their "Épreuve"
# wording — the protocol enumerates them directly, not a paraphrase.
EPREUVES = (
    "Clone déplacé et liens relatifs",
    "Tâche dans chacun des quatre runtimes",
    "Expérience positive, négative et quasi-accident",
    "Travail de routine sans fait significatif",
    "Capture après fusion et sessions concurrentes",
    "Rêve avec cas similaires aux résultats opposés",
    "Deux passages et une source corrigée",
    "Retrait d’une affirmation et frontière d’autorité",
    "Note native contradictoire ou absente",
    "Rêve interrompu ou intégration refusée",
)

# Exploratory smokes excluded from the acceptance count, by merge commit.
SMOKE_MERGES = (
    "ff9465b8",  # #1109 pilot read-before-action smoke
    "758785ca",  # #1117 capture pinning
    "d68c57da",  # #1119 first dream result
    "5fed3482",  # #1127 wave 1 lair dream suggestion
    "87ee07a8",  # #1134 wave 2 v8 markdown smoke
    "d1c57bb3",  # #1135 wave 3 three-runtime evidence
)

REQUIRED_SECTIONS = (
    "## Inputs and versions",
    "## Scenarios",
    "## Denominators and margins",
    "## Evidence surfaces",
    "## Independent verdict",
    "## Exploratory smokes excluded",
)


def relative_targets(text):
    """Markdown link targets that are repo-relative (scheme-less)."""
    return [
        target
        for target in LINK.findall(text)
        if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target)
    ]


def test_protocol_enumerates_every_design_section9_trial():
    text = PROTOCOL.read_text(encoding="utf-8")
    for epreuve in EPREUVES:
        assert epreuve in text, f"protocol lost design §9 trial {epreuve!r}"


def test_protocol_carries_required_sections():
    text = PROTOCOL.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert section in text, f"protocol lost its {section!r} section"


def test_protocol_declares_versions_and_denominators():
    text = PROTOCOL.read_text(encoding="utf-8")
    # Versions: design, DREAM prompt revision, review contract, four runtimes.
    assert "2026-09-10-dragon-memory-design.md" in text
    assert "DREAM" in text and "revision" in text
    for runtime in ("Vibe CLI", "Claude Code", "Codex", "Pi"):
        assert runtime in text, f"protocol omits runtime {runtime!r}"
    # Denominators and margins are predeclared, not a computed score.
    assert "denominator" in text.lower()
    assert "margin" in text.lower()
    assert "no numeric scorer" in text


def test_protocol_names_every_case_class():
    text = PROTOCOL.read_text(encoding="utf-8").lower()
    for case in ("positive", "negative", "near-miss", "no-event"):
        assert case in text, f"protocol omits the {case!r} case class"
    # The two trials the exit criteria single out are explicit.
    assert "contradictory native note" in text
    assert "withdraw" in text


def test_protocol_excludes_smokes_by_commit_reference():
    text = PROTOCOL.read_text(encoding="utf-8")
    for merge in SMOKE_MERGES:
        assert merge in text, f"smoke exclusion lost merge commit {merge}"
    # The ordering constraint itself is stated.
    assert "before the first acceptance trial" in text


def test_protocol_names_the_review_contract_as_a_versioned_input():
    text = PROTOCOL.read_text(encoding="utf-8")
    # Whatever review contract is live on main at trial time, it is named
    # as a versioned input, not a fixed mechanism (F4, 2026-10-02).
    assert "review contract" in text
    assert "at its then-current" in text


def test_protocol_cites_the_attribution_record_format():
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "2026-10-02-reviewer-attribution-design.md" in text
    # §4 fields the trial records must stay convertible to.
    assert "attribution record" in text.lower()


def test_protocol_keeps_mechanical_checks_scripted():
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "wc -l memory/MEMORY.md" in text
    assert "commit" in text.lower()
    assert "link" in text.lower()


def test_protocol_relative_links_resolve():
    text = PROTOCOL.read_text(encoding="utf-8")
    targets = relative_targets(text)
    assert targets, "protocol should cite its inputs by relative link"
    for target in targets:
        resolved = (PROTOCOL.parent / target).resolve()
        assert resolved.exists(), f"broken relative link {target!r}"
        assert resolved == REPO or REPO in resolved.parents, (
            f"link escapes the repository: {target!r}"
        )
