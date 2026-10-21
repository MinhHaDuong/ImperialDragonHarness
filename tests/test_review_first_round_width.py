"""Guard the mechanical first-round panel width and its escape (ticket 0392)."""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "skills/review-pr/SKILL.md"
HUNT = ROOT / "skills/hunt/SKILL.md"
GAZE = ROOT / "skills/gaze/SKILL.md"
CONFIG = ROOT / "skills/review-pr/panel-width.json"


def test_round_one_has_configured_single_seat_criterion():
    config = json.loads(CONFIG.read_text())
    assert config["max_lines"] > 0
    assert config["max_files"] > 0
    assert config["pipeline_paths"]
    text = REVIEW.read_text()
    assert "panel-width.json" in text
    assert "Correctness only" in text
    assert "review:standard" in text
    assert "escalate" in text.lower()
    assert "Round 1 always runs the full proportional" not in text
    assert "**Skip PR**" not in text


def test_callers_preserve_first_round_width_and_override():
    hunt = HUNT.read_text()
    gaze = GAZE.read_text()
    assert "panel-width.json" in hunt
    assert "review:standard" in gaze
    assert "review:standard" in hunt


def test_gaze_always_runs_agent_c_and_defers_width_to_review_pr():
    gaze = GAZE.read_text()
    # Both ends must exist, or the slice silently grows to the whole file.
    assert "**Agent C — PR review**" in gaze and "Wait for all spawned agents" in gaze
    agent_c = gaze.split("**Agent C — PR review**", 1)[1].split("Wait for all spawned agents", 1)[0]
    assert "tier" not in agent_c.lower()
    assert "panel-width.json" in agent_c
    assert "regardless of the risk" not in agent_c
    assert "max_lines" in agent_c and "max_files" in agent_c
    assert "pipeline_paths" in agent_c
    assert "at least" in agent_c and "Correctness + Consistency" in agent_c
