"""Ticket 0918 STEP B — the acceptance-trial results ledger stays in shape.

The predeclared protocol (docs/memory-v8/evaluation-protocol.md, committed
to main before the first acceptance trial) fixes the denominators — 31
cells — and the verdict vocabulary. This module pins the results document's
shape so the ledger cannot silently lose a cell, gain an invented verdict,
or drop the rollout verdict; it does not and cannot certify that any cell's
evidence is truthful — that is what the evidence pointers are for.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "docs" / "memory-v8" / "evaluation-results.md"
PROTOCOL = REPO / "docs" / "memory-v8" / "evaluation-protocol.md"

# Denominators as predeclared by the protocol's § Denominators and margins.
EXPECTED_CELLS = {
    "S1.1": 1,
    "S2": 4,
    "S3": 12,
    "S4": 4,
    "S5": 2,
    "S6.1": 1,
    "S7.1": 1,
    "S8.1": 1,
    "S9": 4,
    "S10.1": 1,
}
CELL_VERDICTS = {"pass", "no-event", "near-miss", "fail", "absent"}
SCENARIO_VERDICTS = {"pass", "near-miss", "fail"}
ROLLOUTS = {"Rollout", "Rollout with recorded limits", "No rollout"}

ROW = re.compile(r"^\|\s*(S[0-9]+[^|]*?)\s*\|\s*([a-z-]+)\s*\|", re.MULTILINE)


def ledger_rows(text):
    """(cell_id, verdict) pairs from the cell ledger table only."""
    section = re.search(
        r"^## Cell ledger.*?(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    if section is None:
        return []
    return [(cell.strip(), verdict) for cell, verdict in ROW.findall(section.group(0))]


def test_results_document_exists_with_protocol_reference():
    text = RESULTS.read_text(encoding="utf-8")
    # The protocol is the versioned input; the results name the revision
    # they ran under (committed to main before the first trial).
    assert "evaluation-protocol.md" in text
    assert re.search(r"protocol revision[^\n]*0a0714ea", text), (
        "results must cite the protocol blob revision on main"
    )


def test_ledger_carries_every_predeclared_cell():
    text = RESULTS.read_text(encoding="utf-8")
    rows = ledger_rows(text)
    assert len(rows) == 31, f"expected 31 predeclared cells, found {len(rows)}"
    for prefix, count in EXPECTED_CELLS.items():
        found = [cell for cell, _ in rows if cell == prefix or cell.startswith(prefix + ".")]
        assert len(found) == count, (
            f"{prefix}: expected {count} cells, found {len(found)}: {found}"
        )
    # Per the four runtimes: S2, S3, S4, S9 each span all four.
    for prefix in ("S2", "S3", "S4", "S9"):
        found = [cell for cell, _ in rows if cell.startswith(prefix + ".")]
        for runtime in ("vibe", "claude", "codex", "pi"):
            assert any(runtime in cell for cell in found), (
                f"{prefix} loses its {runtime} cell"
            )


def test_every_cell_verdict_is_in_the_predeclared_vocabulary():
    text = RESULTS.read_text(encoding="utf-8")
    for cell, verdict in ledger_rows(text):
        assert verdict in CELL_VERDICTS, f"{cell}: verdict {verdict!r} not predeclared"


def test_every_scenario_has_a_verdict_line():
    text = RESULTS.read_text(encoding="utf-8")
    for prefix in EXPECTED_CELLS:
        match = re.search(rf"^\| {re.escape(prefix)}[.0]? \| (\w[\w-]*)", text, re.MULTILINE)
        if match is None:
            # S1.1/S6.1/S7.1/S8.1/S10.1 are their own cells; scenario verdict
            # equals cell verdict unless stated otherwise.
            continue
        assert match.group(1).lower() in SCENARIO_VERDICTS | CELL_VERDICTS, (
            f"{prefix}: scenario verdict {match.group(1)!r} not predeclared"
        )
    # Each scenario section names its verdict explicitly.
    for scenario in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"):
        section = re.search(rf"^## {scenario} — .*?(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
        assert section, f"results lost their {scenario} section"
        assert re.search(r"verdict[^\n]*", section.group(0), re.IGNORECASE), (
            f"{scenario} section states no verdict"
        )


def test_versions_and_conditions_are_recorded():
    text = RESULTS.read_text(encoding="utf-8")
    for marker in ("Vibe CLI", "Claude Code", "Codex", "Pi"):
        assert marker in text, f"results omit the {marker} trial version"
    # Every trial records runtime, model and conditions per the protocol.
    assert "model" in text.lower()
    assert "DREAM" in text and "v8-r1" in text
    # The review contract is named as a versioned input.
    assert "review contract" in text.lower()
    assert "b401f134fe48" in text, "results must cite the review-contract blob"


def test_case_classes_and_explicit_trials_are_present():
    text = RESULTS.read_text(encoding="utf-8").lower()
    for case in ("positive", "negative", "near-miss", "no-event"):
        assert case in text, f"results omit the {case!r} case class"
    assert "contradictory native note" in text
    assert "withdrawn" in text


def test_rollout_verdict_is_explicit_and_predeclared():
    text = RESULTS.read_text(encoding="utf-8")
    assert "## Rollout verdict" in text
    verdicts = [v for v in ROLLOUTS if re.search(rf"^\*\*{v}\*\*", text, re.MULTILINE)]
    assert len(verdicts) == 1, "exactly one of the three predeclared verdicts"
    # Margins not invented after a successful example: the verdict cites
    # the protocol's rule, not a new one.
    assert "zero fail" in text.lower() or "any scenario fails" in text.lower()


def test_attribution_convertible_review_facts_are_recorded():
    text = RESULTS.read_text(encoding="utf-8")
    assert "reviewer" in text.lower()
    # Attribution-record fields: runtime/model/version, path:line anchors,
    # adopted yes/no (attribution design §4).
    assert re.search(r"path:line|:\d+", text)
    assert re.search(r"adopted: (yes|no)", text)


def test_results_links_resolve():
    text = RESULTS.read_text(encoding="utf-8")
    targets = [
        target
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)", text)
        if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target)
    ]
    assert targets, "results should point at evidence by relative link"
    for target in targets:
        resolved = (RESULTS.parent / target).resolve()
        assert resolved.exists(), f"broken relative link {target!r}"
