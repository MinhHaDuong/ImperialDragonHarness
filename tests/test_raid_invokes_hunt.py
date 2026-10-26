"""Guard: raid must invoke /hunt mechanically, not paraphrase it.

Child of ticket 0293 (tracking 0251, Option A: skill-invokes-skill). The
execute-agent contract's FIRST action must be an imperative, greppable
Skill-invocation of hunt — not a prose paraphrase like "follows /hunt
workflow", which is exactly what drifted between the aedist Wave A and Wave B
prompts (2026-06-11/12). Only the negative guard (the known paraphrase stays
gone) and hunt's model-invocable frontmatter are checked; the author judged
positive pins of raid's wording a poor guard. Fast tier, no marker.
"""

from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "raid" / "SKILL.md"


def test_phase5_does_not_paraphrase_hunt():
    """The prose paraphrase must be gone — the skill loader is the contract."""
    assert "follows `/hunt` workflow" not in SKILL.read_text(), (
        "Phase 5 still paraphrases hunt ('follows `/hunt` workflow'); the "
        "agent prompt must invoke the skill, not describe what it does"
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
