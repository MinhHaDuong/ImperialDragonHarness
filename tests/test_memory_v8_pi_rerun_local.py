"""Ticket 1022 — the pi local-provider re-run evidence doc stays in shape.

The re-run of the interrupted Pi acceptance cells ran on the local
provider (llama.cpp on Padme, qwen3.8-27b through pi's "padme" entry), a
declared changed input per the protocol's version discipline, under the
unchanged protocol margins. This module pins the evidence document's
mechanically pinnable shape: it must cite the unchanged protocol
revision, the original cells it re-runs, the changed input named as
pi-with-qwen3.8-27b, the versions recorded from pi's own session header
and the server's metadata (never the model's self-description), the
corrected S9 channel map, exactly one explicit verdict line per re-run
cell in the predeclared vocabulary, a blocker disposition consistent
with those verdicts, and limits plus disposal sections. It also pins
that the closed acceptance ledger still carries the original pi fails
and absent — this re-run must not have edited it — and that 0913's log
carries the result. Truthfulness of the recorded evidence is not this
module's to certify; the pointers and hashes are for that.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RERUN = REPO / "docs" / "memory-v8" / "2026-10-02-pi-rerun-local-provider.md"
RESULTS = REPO / "docs" / "memory-v8" / "evaluation-results.md"
TICKETS = REPO / "tickets"

CELL_VERDICTS = {"pass", "fail", "near-miss", "no-event", "absent"}
VERDICT_LINE = re.compile(
    r"^\*\*Cell (S3\.negative|S3\.near-miss|S3\.positive|S4|S9)\.pi re-run verdict: "
    r"(pass|fail|near-miss|no-event|absent)\.\*\*$",
    re.MULTILINE,
)
EXPECTED_CELLS = {"S3.negative", "S3.near-miss", "S3.positive", "S4", "S9"}


def test_rerun_doc_exists_and_cites_unchanged_protocol():
    text = RERUN.read_text(encoding="utf-8")
    assert "evaluation-protocol.md" in text
    # The re-run ran under the same protocol blob revision as the original
    # acceptance trial and the S9.codex re-trial; a changed margin would
    # need a new trial.
    assert re.search(r"protocol revision 0a0714ea[0-9a-f]*", text), (
        "re-run must cite the unchanged protocol blob revision"
    )


def test_rerun_cites_the_original_cells_it_re_runs():
    text = RERUN.read_text(encoding="utf-8")
    assert "evaluation-results.md" in text
    # The original verdicts are named, not smoothed away.
    for cell in ("S3.negative.pi", "S3.near-miss.pi", "S3.positive.pi", "S4.pi"):
        assert re.search(rf"{re.escape(cell)}\s*=\s*\*\*fail\*\*", text), (
            f"the original {cell} fail must be named"
        )
    assert "S9.pi = **absent**" in text


def test_changed_input_is_declared_and_named():
    text = RERUN.read_text(encoding="utf-8")
    assert "Changed input, declared" in text
    # Verdicts are for pi-with-qwen3.8-27b, never presented as re-runs
    # under the trial's metered Kimi-K2.6.
    assert "pi-with-qwen3.8-27b" in text
    assert "Kimi-K2.6" in text
    assert "padme" in text


def test_versions_recorded_from_runtime_sources():
    text = RERUN.read_text(encoding="utf-8")
    assert "0.87.1" in text
    assert "printed header" in text
    assert "model_change" in text
    assert "qwen3.8-27b" in text
    assert "llamacpp" in text
    # Versions come from pi's own session header and the server's
    # metadata, never the model's self-description.
    assert "never from the model's self-description" in text
    # The disposable session record is cited by hash, not by a live path.
    assert re.search(r"sha256 d75cb397[0-9a-f]*", text)
    # The prompt is the original trial's, verbatim, by hash.
    assert "439a4c18f816c5a7fadab2388a3accf2abc6dddfa4f88d3b5b4a5b8cc0bc59db" in text


def test_corrected_s9_channel_map_is_recorded():
    text = RERUN.read_text(encoding="utf-8")
    # Per-directory first-match candidates, in order.
    assert "AGENTS.override.md" in text
    assert "CLAUDE.MD" in text
    assert "PI_CODING_AGENT_DIR" in text
    # The original plant missed because AGENTS.md shadows same-directory
    # CLAUDE.md; the corrected plant went to a channel pi really loads.
    assert "shadows" in text or "shadowed" in text
    assert "global" in text
    # Delivery was verified mechanically, with counts.
    assert "project-instruction" in text or "project_instructions" in text
    assert "14 occurrences" in text


def test_exactly_one_explicit_verdict_line_per_rerun_cell():
    text = RERUN.read_text(encoding="utf-8")
    matches = VERDICT_LINE.findall(text)
    cells = {cell for cell, _ in matches}
    assert len(matches) == 5, "exactly five explicit cell verdict lines"
    assert cells == EXPECTED_CELLS, "one verdict line per re-run cell"
    for _, verdict in matches:
        assert verdict in CELL_VERDICTS


def test_blocker_disposition_consistent_with_verdicts():
    text = RERUN.read_text(encoding="utf-8")
    verdicts = {verdict for _, verdict in VERDICT_LINE.findall(text)}
    assert "Blocker disposition:" in text, (
        "the doc must state the blocker disposition explicitly"
    )
    if verdicts == {"pass", "no-event"}:
        assert "no acceptance-trial blocker remains recorded" in text, (
            "all-pass re-run resolves the 0913 blocker exactly as recorded"
        )
    else:
        assert "author" in text, (
            "a non-passing re-run must hand the disposition to the author"
        )


def test_limits_and_disposal_are_recorded():
    text = RERUN.read_text(encoding="utf-8")
    assert "## Limits, recorded not smoothed" in text
    assert "## Disposal" in text
    assert "/tmp/pirerun" in text
    assert "deleted" in text.lower()
    flat = " ".join(text.split())
    assert "primary checkout and local main were never touched" in flat
    # The weaker-model condition is named as a limit, not smoothed.
    assert "weaker model" in text


def test_closed_acceptance_ledger_still_carries_the_original_cells():
    results = RESULTS.read_text(encoding="utf-8")
    # This re-run must not have edited the closed ledger: the original
    # cell verdicts stand there, unchanged.
    for cell in ("S3.negative.pi", "S3.near-miss.pi", "S3.positive.pi", "S4.pi"):
        assert re.search(rf"\|\s*{re.escape(cell)}\s*\|\s*fail\s*\|", results), (
            f"the closed acceptance ledger must keep its recorded {cell} fail"
        )
    assert re.search(r"\|\s*S9\.pi\s*\|\s*absent\s*\|", results), (
        "the closed acceptance ledger must keep its recorded S9.pi absent"
    )


def test_0913_log_carries_the_result():
    ticket = next(TICKETS.glob("0913-*.erg"))
    text = ticket.read_text(encoding="utf-8")
    assert "1022" in text
    assert "pass/pass/pass/no-event/pass" in text
    assert "pi-with-qwen3.8-27b" in text
    assert "2026-10-02-pi-rerun-local-provider.md" in text


def test_capture_entry_is_committed_as_the_positive_cell_evidence():
    entry = (
        REPO
        / "memory"
        / "journal"
        / "2026"
        / "2026-10-02-memory-v8-0918-pi-native-load-delivered-contradictory-note.md"
    )
    assert entry.exists(), "the pi session's capture must be on the branch"
    text = entry.read_text(encoding="utf-8")
    # Factual capture boundaries: no rule proposal, no lesson-drawing.
    assert "obsolete and superseded" in text
    assert "Uncertainty" in text


def test_rerun_doc_links_resolve():
    text = RERUN.read_text(encoding="utf-8")
    targets = [
        target
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)", text)
        if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target)
    ]
    assert targets, "the doc should point at evidence by relative link"
    for target in targets:
        resolved = (RERUN.parent / target).resolve()
        assert resolved.exists(), f"broken relative link {target!r}"
