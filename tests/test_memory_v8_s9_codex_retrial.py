"""Ticket 1019 — the S9.codex re-trial evidence doc stays in shape.

The re-trial of the failed S9.codex acceptance cell ran under the closed
user-level AGENTS.md channel (author decision 2026-10-02, ticket 1019).
This module pins the evidence document's mechanically pinnable shape: it
must cite the unchanged protocol revision, the original S9 result it
re-tries, the preflight that closes the channel, the plant channel and its
delivery status, an explicit cell verdict in the predeclared vocabulary,
and a blocker disposition consistent with that verdict. It also pins that
the closed acceptance ledger still carries the original fail — this
re-trial must not have edited it — and that 0913's log carries the
result. Truthfulness of the recorded evidence is not this module's to
certify; the pointers and hashes are for that.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RETRIAL = REPO / "docs" / "memory-v8" / "2026-10-02-s9-codex-retrial-closed-channel.md"
RESULTS = REPO / "docs" / "memory-v8" / "evaluation-results.md"
TICKETS = REPO / "tickets"

CELL_VERDICTS = {"pass", "fail", "near-miss", "absent"}
VERDICT_LINE = re.compile(
    r"^\*\*Cell S9\.codex re-trial verdict: (pass|fail|near-miss|absent)\.?\*\*\.?$",
    re.MULTILINE,
)


def test_retrial_doc_exists_and_cites_unchanged_protocol():
    text = RETRIAL.read_text(encoding="utf-8")
    assert "evaluation-protocol.md" in text
    # The re-trial ran under the same protocol blob revision as the
    # original acceptance trial; a changed margin would need a new trial.
    assert re.search(r"protocol revision 0a0714ea[0-9a-f]*", text), (
        "re-trial must cite the unchanged protocol blob revision"
    )


def test_retrial_cites_the_original_failed_cell():
    text = RETRIAL.read_text(encoding="utf-8")
    assert "evaluation-results.md" in text
    assert "S9.codex" in text
    # The original verdict is named, not smoothed away.
    assert re.search(r"S9\.codex = \*\*fail\*\*", text) or "cell verdict S9.codex = **fail**" in text


def test_preflight_and_plant_channel_are_recorded():
    text = RETRIAL.read_text(encoding="utf-8")
    # Decision 1's one-line preflight, with its result.
    assert "test ! -f ~/.codex/AGENTS.md" in text
    assert re.search(r"^\*\*PASS\*\*", text, re.MULTILINE) or "**PASS**" in text
    # The plant went to the remaining rules/ channel, with its hash.
    assert "rules/s9-supersession.rules" in text
    assert re.search(r"sha256 [0-9a-f]{64}", text)
    # The contradictory claim is identified.
    assert "obsolete and superseded" in text


def test_delivery_status_is_recorded_mechanically():
    text = RETRIAL.read_text(encoding="utf-8")
    # Delivery was verified from codex's own tooling, with counts.
    assert "codex debug prompt-input" in text
    assert "codex execpolicy check" in text
    assert "0 occurrences" in text


def test_explicit_verdict_in_predeclared_vocabulary():
    text = RETRIAL.read_text(encoding="utf-8")
    verdicts = VERDICT_LINE.findall(text)
    assert len(verdicts) == 1, "exactly one explicit cell verdict line"
    assert verdicts[0] in CELL_VERDICTS


def test_blocker_disposition_matches_verdict():
    text = RETRIAL.read_text(encoding="utf-8")
    verdict = VERDICT_LINE.search(text).group(1)
    disposition = re.search(r"\*\*Blocker disposition: (.+?)\.\*\*", text)
    assert disposition, "the doc must state the blocker disposition explicitly"
    stated = disposition.group(1).rstrip(".")
    if verdict == "pass":
        assert stated == "channel closed, re-trial passed", (
            "a passing re-trial downgrades the blocker exactly as the author decided"
        )
    else:
        assert "author" in stated, (
            "a non-passing re-trial must hand the restricted-runtime fallback to the author"
        )


def test_versions_recorded_from_runtime_sources():
    text = RETRIAL.read_text(encoding="utf-8")
    assert "codex-cli 0.159.3" in text
    assert "gpt-6.1-sol" in text
    assert "printed header" in text or "own event stream" in text
    # The stream is cited by hash, not by a live disposable path.
    assert "80178664df5ae1bb" in text


def test_limits_and_disposal_are_recorded():
    text = RETRIAL.read_text(encoding="utf-8")
    assert "## Limits, recorded not smoothed" in text
    assert "## Disposal" in text
    assert "/tmp/s9retry1019" in text
    assert "deleted" in text.lower()


def test_closed_acceptance_ledger_still_carries_the_original_fail():
    results = RESULTS.read_text(encoding="utf-8")
    # This re-trial must not have edited the closed ledger: the original
    # cell verdict stands there, unchanged.
    assert re.search(r"\|\s*S9\.codex\s*\|\s*fail\s*\|", results), (
        "the closed acceptance ledger must keep its recorded S9.codex fail"
    )


def test_0913_log_carries_the_result_and_the_standing_condition():
    ticket = next((TICKETS / "closed").glob("0913-*.erg"))
    text = ticket.read_text(encoding="utf-8")
    assert "channel closed, re-trial passed" in text
    assert "no user-level ~/.codex/AGENTS.md" in text
    assert "1019" in text


def test_retrial_links_resolve():
    text = RETRIAL.read_text(encoding="utf-8")
    targets = [
        target
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)", text)
        if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target)
    ]
    assert targets, "the doc should point at evidence by relative link"
    for target in targets:
        resolved = (RETRIAL.parent / target).resolve()
        assert resolved.exists(), f"broken relative link {target!r}"
