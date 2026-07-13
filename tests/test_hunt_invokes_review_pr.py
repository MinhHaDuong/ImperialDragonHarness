"""Guard: hunt step 11 must invoke /review-pr mechanically, not paraphrase it.

Child of ticket 0307 (roar sweep after the 0251 raid). Ticket 0293 replaced
raid Phase 5's "follows /hunt workflow" paraphrase with a mechanical
Skill(hunt) invocation, because paraphrases drift. The same shape survived in
skills/hunt/SKILL.md step 11 — "Review according to /review-pr" — which an
executing agent may paraphrase instead of invoking the skill. review-pr sets
disable-model-invocation: false, so the mechanical call works. Text-grep only
→ fast tier, no marker.
"""

from pathlib import Path

HUNT = Path(__file__).resolve().parent.parent / "skills" / "hunt" / "SKILL.md"


def test_step11_invokes_review_pr_mechanically():
    """The imperative Skill-invocation string must be present in hunt."""
    text = HUNT.read_text()
    assert 'Skill(skill: "review-pr", args:' in text, (
        "hunt step 11 must invoke the mechanical "
        'Skill(skill: "review-pr", args: <pr-number>), not a paraphrase'
    )


def test_step11_does_not_paraphrase_review_pr():
    """The prose paraphrase must be gone — the skill loader is the contract."""
    text = HUNT.read_text()
    assert "Review according to `/review-pr`" not in text, (
        "hunt step 11 still paraphrases review-pr ('Review according to "
        "`/review-pr`'); the agent prompt must invoke the skill, not describe it"
    )


def test_review_pr_is_model_invocable():
    """The mandated Skill(review-pr) call only works if model invocation is on."""
    review_pr = HUNT.parent.parent / "review-pr" / "SKILL.md"
    frontmatter = review_pr.read_text().split("---")[1]
    assert "disable-model-invocation: false" in frontmatter, (
        "skills/review-pr/SKILL.md must set disable-model-invocation: false — "
        "hunt step 11 mandates Skill(review-pr), which the Skill tool refuses "
        "while model invocation is disabled"
    )
