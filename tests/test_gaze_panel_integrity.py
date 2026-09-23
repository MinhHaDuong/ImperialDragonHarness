"""Ticket 0928: an Agent C panel cannot claim independent agreement without fan-out."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_agent_c_launch_grants_nested_agent_tool():
    gaze = (ROOT / "skills/gaze/SKILL.md").read_text()
    profile = ROOT / "agents/gaze-pr-review.md"
    assert profile.exists(), "Agent C needs a named profile with an explicit tool grant"
    frontmatter = profile.read_text().split("---", 2)[1]
    tools = re.search(r"^tools:\s*(.+)$", frontmatter, re.MULTILINE)
    assert tools and "Agent" in [item.strip() for item in tools.group(1).split(",")]
    agent_c = gaze.split("**Agent C — PR review**", 1)[1].split(
        "Wait for all spawned agents", 1
    )[0]
    assert "subagent_type: gaze-pr-review" in agent_c


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
