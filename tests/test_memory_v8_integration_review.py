"""Ticket 0909 — the integration review's mechanically pinnable shape.

The integration review (docs/memory-v8/integration-review.md) verifies the
tracker's five exit criteria against the delivered record. This module pins
what a machine can pin: the document exists and is dated, every relative
link resolves, each of the five criteria has its own section stating a
verdict, and the author's 0913 scope decision is cited with its No-rollout
verdict and PR. It cannot certify the review's judgment — that is what the
evidence citations in the document are for.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REVIEW = REPO / "docs" / "memory-v8" / "integration-review.md"

LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")
CRITERION = re.compile(r"^## Criterion [1-5] — ", re.MULTILINE)
SCOPE_DECISION = "SCOPE DECISION (author, 2026-10-02, on the predeclared"


def relative_links(text):
    return [
        target
        for target in LINK.findall(text)
        if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target)
    ]


def test_review_exists_and_is_dated():
    text = REVIEW.read_text(encoding="utf-8")
    assert "2026-10-02" in text, "the review must carry its date"


def test_every_relative_link_resolves():
    """Links are relative to the review's own directory, like the pilot test."""
    broken = []
    for target in relative_links(REVIEW.read_text(encoding="utf-8")):
        resolved = (REVIEW.parent / target).resolve()
        if not resolved.is_relative_to(REPO.resolve()):
            broken.append(f"{target} (escapes the repo)")
        elif not resolved.is_file():
            broken.append(target)
    assert not broken, f"unresolved links: {broken}"


def test_all_five_criteria_present_with_verdicts():
    text = REVIEW.read_text(encoding="utf-8")
    assert CRITERION.findall(text) == [
        f"## Criterion {n} — " for n in range(1, 6)
    ], "the five tracker exit criteria each need their own section"
    assert text.count("Verdict: MET.") >= 5, "every criterion section states its verdict"


def test_scope_decision_cited_with_verdict_and_pr():
    text = REVIEW.read_text(encoding="utf-8")
    # The author's 0913 scope decision is quoted verbatim, with the
    # predeclared No-rollout verdict and the PR that recorded it.
    assert SCOPE_DECISION in text, "the review must cite the scope decision"
    assert "No rollout" in text, "the review must name the recorded verdict"
    assert "PR #1142" in text, "the review must cite the trials PR"
    assert "0913 stays open" in text, "the review must state 0913 stays open"
