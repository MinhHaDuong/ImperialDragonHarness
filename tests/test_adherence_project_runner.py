"""Keep the declared project runner authoritative across both skill callers."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parent.parent


def test_adherence_discovers_a_declared_runner_and_fails_closed():
    text = (REPO / "skills/verify-adherence/SKILL.md").read_text()
    assert "### 1. Project runner (never skip)" in text
    runner = text.split("### 1. Project runner (never skip)", 1)[1].split("### ", 1)[0]
    for contract in (
        "project instructions", "build file", "CI", "verbatim",
        "no declared adherence runner", "adherence: FAIL",
        "verify-adherence#project-runner", "ESCALATE",
    ):
        assert contract in runner, f"Missing runner contract: {contract}"
    assert not re.search(r"uv run|pytest|pyproject|ruff", text)


def test_gaze_loads_live_adherence_contract():
    text = (REPO / "skills/gaze/SKILL.md").read_text()
    agent_a = text.split("**Agent A — adherence**", 1)[1].split("**Agent B", 1)[0]
    assert 'Skill(skill: "verify-adherence"' in agent_a
    assert "harness-extension-point: runtime skill-loader invocation" in agent_a
    assert "worktree=" in agent_a
    assert "structured" in agent_a
    assert not re.search(r"uv run|pytest|pyproject|ruff", agent_a)


def test_trace_doctor_uses_harness_stdlib_interpreter():
    text = (REPO / "skills/trace-doctor/SKILL.md").read_text()
    assert "uv run" not in text
    for script in ("trace-stats", "trace-compact-audit", "trace-pr-join", "trace-hypotheses"):
        assert f'python3 "$HARNESS_DIR/scripts/{script}.py"' in text
