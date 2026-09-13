"""Guard the raid Imagine team's cross-ticket Blind-Spot pass.

The pass exists to challenge the search space considered by the per-ticket
Imagine agents, not to duplicate implementation review. Keep the checks
bounded to Phase 2 so unrelated prose cannot satisfy them accidentally.
"""

from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "raid" / "SKILL.md"


def _phase2() -> str:
    text = SKILL.read_text()
    start = text.find("## Phase 2: Imagine")
    assert start != -1, "Phase 2 (Imagine) header missing"
    end = text.find("## Phase 3: Plan", start)
    assert end != -1, "Phase 3 header missing (cannot bound Phase 2)"
    return text[start:end]


def test_blind_spot_runs_after_parallel_imagine_agents():
    phase2 = _phase2()
    wait = phase2.find("Wait for all.")
    blind = phase2.find("### Blind-Spot pass")
    assert wait != -1 and blind > wait, (
        "Blind-Spot must be a collective pass after all per-ticket Imagine agents return"
    )


def test_blind_spot_reads_the_whole_team_output():
    phase2 = _phase2()
    assert "one" in phase2[phase2.find("### Blind-Spot pass") :].lower()
    assert "all\nImagine outputs together" in phase2, (
        "Blind-Spot must inspect all Imagine outputs together, not run as another per-ticket seat"
    )


def test_blind_spot_challenges_search_space_not_implementation_review():
    phase2 = _phase2()
    blind = phase2[phase2.find("### Blind-Spot pass") :]
    assert "search space" in blind
    assert "not to review implementation quality" in blind
    for lens in ("assumptions", "stakeholders", "evidence", "alternative", "failure modes"):
        assert lens in blind, f"Blind-Spot lens missing: {lens}"


def test_blind_spot_preserves_author_intent_boundary():
    phase2 = _phase2()
    blind = phase2[phase2.find("### Blind-Spot pass") :]
    assert "may not invent a new deliverable" in blind
    assert "returned to the author" in blind
