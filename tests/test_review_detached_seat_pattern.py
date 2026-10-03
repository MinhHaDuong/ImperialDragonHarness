"""Detached-seat substitution pattern pins (ticket 1017).

Child sessions spawned through a runtime's agent connector do not expose
the connector themselves: ``tools.agent`` was absent in every child
session of the 2026-10-02 raid on 0853/0937/0979/1014 (PRs #1129-#1132),
so every skill that asks a child to spawn reviewer seats — hunt step 11's
review-pr, gaze phases 2-4/6 — fails its panel exactly there. The
substitution that works — one detached headless non-interactive CLI
process per seat, prompt-embedded seat contract, worktree-pinned cwd,
artifact polling — was rediscovered independently by every session that
hit the wall, twice mis-launched first, and is now documented once in
skills/review-pr/SKILL.md.

These tests pin the section and its two pointers (review-pr fan-out
preflight, gaze Agent C) so the pattern cannot drift back to an
undocumented per-session rediscovery.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

HEADING = "### Detached-seat substitution"


def _section(text: str) -> str:
    assert HEADING in text, "review-pr must document the detached-seat substitution"
    return text.split(HEADING, 1)[1].split("### ", 1)[0]


def test_review_pr_documents_detached_seat_contract():
    review = (REPO / "skills" / "review-pr" / "SKILL.md").read_text()
    section = _section(review)
    # One detached headless CLI process per seat, contract embedded in the prompt.
    assert "non-interactive" in section
    assert "detached" in section
    assert "prompt" in section
    assert "worktree" in section
    assert "cwd" in section
    assert "read-only" in section
    assert "deny-rules" in section
    assert "one string" in section or "single string" in section
    assert "model" in section
    assert "limitation" in section
    # Completion by artifact polling under the existing concurrency contract.
    assert ".part" in section
    assert "rename" in section
    assert "concurrency contract" in section
    # Spawn success is never a completion signal (raid-1008).
    assert "spawn" in section
    assert "success" in section
    assert "never trust" in section or "not trust" in section
    # Slot budget / child cap absorbed from the 0980/1009 blind-spot note.
    assert "slot budget" in section or "child cap" in section
    assert "no report" in section or "no-report" in section
    # Runtime-portable, not a claude-only recipe.
    lower = section.lower()
    assert "vibe" in lower
    assert "claude" in lower
    # seat-runner.sh stays an optional heavier transport, never required.
    assert "seat-runner.sh" in section
    assert "optional" in section or "heavier" in section


def test_fanout_preflight_points_to_detached_seat_substitution():
    review = (REPO / "skills" / "review-pr" / "SKILL.md").read_text()
    preflight = review.split("**Fan-out preflight:**", 1)[1].split(
        "| Agent |", 1
    )[0]
    assert "detached-seat substitution" in preflight


def test_gaze_agent_c_points_to_detached_seat_substitution():
    gaze = (REPO / "skills" / "gaze" / "SKILL.md").read_text()
    agent_c = gaze.split("**Agent C — PR review**", 1)[1].split(
        "Wait for all spawned agents", 1
    )[0]
    assert "detached-seat substitution" in agent_c
    assert "review-pr" in agent_c
