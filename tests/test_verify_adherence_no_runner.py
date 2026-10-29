"""verify-adherence degrades to a visible skip when a project declares no runner."""

import re
from pathlib import Path

SKILL = (Path(__file__).resolve().parents[1] / "skills/verify-adherence/SKILL.md").read_text()


def _phase1() -> str:
    start = SKILL.index("### 1. Project runner")
    return SKILL[start : SKILL.index("\n### ", start + 1)]


def test_no_declared_runner_is_a_skip_with_reason():
    text = _phase1()
    para = text[text.index("If none is declared") :].split("\n\n")[0]
    assert "mechanical_runner: skipped (no declared adherence runner)" in para
    assert "blocking" not in para
    assert "adherence: FAIL" not in para
    assert "mechanical_runner:" in SKILL[SKILL.index("### 4. Emit verdict") :]
    breaker = re.search(r"- No declared adherence runner[^\n]*", SKILL).group(0)
    assert "FAIL" not in breaker and "skip" in breaker


def test_declared_but_unrunnable_runner_still_escalates():
    para = _phase1()
    assert "missing is an\nenvironment error: ESCALATE" in para
    assert "- A declared runner cannot execute → ESCALATE" in SKILL


def test_declared_runner_behaviour_unchanged():
    text = _phase1()
    assert "Invoke the declared command verbatim from the project worktree" in text
    assert "A non-zero\ntest/check result is blocking" in text
    assert "verify-adherence#project-runner" in text


def test_verdict_mapping_admits_the_skipped_runner():
    mapping = SKILL[SKILL.index("PASS requires successful mechanical checks") :].split("\n\n")[0]
    assert "skipped" in mapping.split("no blocking semantic findings")[0]
