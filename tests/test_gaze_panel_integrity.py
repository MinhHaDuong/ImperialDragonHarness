"""Ticket 0928: an Agent C panel cannot claim independent agreement without fan-out."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_review_pr_is_invoked_directly_without_a_wrapper_agent():
    gaze = (ROOT / "skills/gaze/SKILL.md").read_text()
    assert not (ROOT / "agents/gaze-pr-review.md").exists()
    assert "gaze-pr-review" not in gaze
    agent_c = gaze.split("**Agent C — PR review**", 1)[1].split(
        "Wait for all spawned agents", 1
    )[0]
    assert "missing at the bounded collection deadline" in agent_c


def test_agent_c_missing_fanout_is_visible_in_both_pr_comments():
    gaze = (ROOT / "skills/gaze/SKILL.md").read_text()
    review = (ROOT / "skills/review-pr/SKILL.md").read_text()
    agent_c = gaze.split("**Agent C — PR review**", 1)[1].split(
        "Wait for all spawned agents", 1
    )[0]
    for text in (agent_c, review):
        assert "PANEL-INTEGRITY:" in text
        assert "dissent: unavailable" in text
        assert "Agent tool" in text
        assert "post" in text.lower()
    output = gaze.split("## Output shape", 1)[1]
    assert "panel integrity:" in output


def test_review_pr_does_not_substitute_sequential_self_review():
    review = (ROOT / "skills/review-pr/SKILL.md").read_text()
    assert "do not run the perspectives sequentially yourself" in review
    assert "no report" in review
    assert "PANEL-INTEGRITY:" in review


def test_preflight_does_not_trust_spawn_success():
    review = (ROOT / "skills/review-pr/SKILL.md").read_text()
    preflight = review.split("**Fan-out preflight:**", 1)[1].split(
        "The remaining review content", 1
    )[0]
    assert "not a guarantee the agent exists" in preflight
    assert "agent.list" in preflight
    assert "source of truth" in preflight
    assert "#1143" in preflight


def test_live_review_surfaces_do_not_dispatch_retired_governance():
    """The live skills must not send an agent back into the old write API.

    Check Gaze setup, Raid recovery, and Coaching's loaded reference;
    removing only the descriptor's command table would leave live callers.
    """
    paths = [ROOT / f"skills/{name}/SKILL.md" for name in
             ("reviewers", "gaze", "raid")]
    paths.append(ROOT / "scripts/coaching/references/replay.md")
    for path in paths:
        text = path.read_text()
        calls = re.findall(r"/reviewers\s+(\w+)", text)
        retired = {"request", "harvest", "scorecard", "scores", "audition", "list"}
        assert not retired.intersection(calls), (path, calls)
        assert not re.search(r"(?:reviewers\.sh|panel(?:-padme)?\.yml)", text), path


def test_retired_reviewer_write_assets_are_absent():
    """A live route must not retain a callable legacy roster/write path."""
    retired = (
        "skills/reviewers/reviewers.sh",
        "skills/reviewers/padme-reviewers.sh",
        "skills/reviewers/panel.yml",
        "skills/reviewers/panel-padme.yml",
        "tests/test_reviewers.sh",
        "tests/test_reviewers_audition.sh",
        "tests/test_padme_reviewers.sh",
    )
    remaining = [name for name in retired if (ROOT / name).exists()]
    assert not remaining, f"retired reviewer write assets remain: {remaining}"


def test_runtime_route_keeps_finding_and_failure_evidence_separate():
    """A clean review and an unavailable review must remain distinguishable.

    Reuse the gate's existing finding classes and integrity records on the new
    route, so an optional provider failure cannot masquerade as zero findings.
    Pointer resolution itself is covered by test_skill_reference_pointers.
    """
    descriptor = (ROOT / "skills/reviewers/SKILL.md").read_text()
    references = re.findall(r"`references/([\w.-]+\.md)`", descriptor)
    assert references, "the runtime route needs its evidence contract"
    route = "\n".join(
        (ROOT / "skills/reviewers/references" / name).read_text()
        for name in references
    )
    for token in ("verifiable:", "consider:", "SEAT-FAILED:",
                  "SEAT-MISSING:", "PANEL-INTEGRITY:"):
        assert token in route, f"runtime route lost gate record {token}"
        assert token in (ROOT / "skills/gaze/SKILL.md").read_text(), token
    assert "scripts/coaching/references/replay.md" in descriptor
