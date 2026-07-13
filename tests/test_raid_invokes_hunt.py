"""Guard: raid Phase 5 must invoke /hunt mechanically, not paraphrase it.

Child of ticket 0293 (tracking 0251, Option A: skill-invokes-skill). The
execute-agent contract's FIRST action must be an imperative, greppable
Skill-invocation of hunt — not a prose paraphrase like "follows /hunt
workflow", which is exactly what drifted between the aedist Wave A and Wave B
prompts (2026-06-11/12). Text-grep only → fast tier, no marker.
"""

from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "raid" / "SKILL.md"


def _phase5() -> str:
    """Return the text of Phase 5 (Execute), up to Phase 6."""
    text = SKILL.read_text()
    start = text.find("## Phase 5: Execute")
    assert start != -1, "Phase 5 (Execute) header missing"
    end = text.find("## Phase 6", start)
    assert end != -1, "Phase 6 header missing (cannot bound Phase 5)"
    return text[start:end]


def test_phase5_invokes_hunt_mechanically():
    """The imperative Skill-invocation string must be present in Phase 5."""
    phase5 = _phase5()
    assert 'Skill(skill: "hunt", args:' in phase5, (
        "Phase 5 must open the execute-agent contract with the mechanical "
        'invocation Skill(skill: "hunt", args: "<id>"), not a paraphrase'
    )


def test_phase5_does_not_paraphrase_hunt():
    """The prose paraphrase must be gone — the skill loader is the contract."""
    phase5 = _phase5()
    assert "follows `/hunt` workflow" not in phase5, (
        "Phase 5 still paraphrases hunt ('follows `/hunt` workflow'); the "
        "agent prompt must invoke the skill, not describe what it does"
    )


def test_phase5_forbids_inlining_hunt_steps():
    """The prohibition against paraphrasing/inlining hunt's steps is stated."""
    phase5 = _phase5()
    assert "paraphrase" in phase5 and "inline" in phase5, (
        "Phase 5 must state that agent prompts do not paraphrase or inline "
        "hunt's steps; the skill loader supplies the live contract"
    )


def test_hunt_is_model_invocable():
    """The mandated Skill(hunt) call only works if hunt allows model invocation."""
    hunt = SKILL.parent.parent / "hunt" / "SKILL.md"
    frontmatter = hunt.read_text().split("---")[1]
    assert "disable-model-invocation: false" in frontmatter, (
        "skills/hunt/SKILL.md must set disable-model-invocation: false — "
        "raid Phase 5 mandates Skill(hunt), which the Skill tool refuses "
        "while model invocation is disabled (hit at runtime, raid 0293)"
    )
