"""Lair step 10 must land STATE.md via a PR, not a local ff-merge (ticket 0261).

On 2026-06-18 a lair run followed step 10's "merge to main via fast-forward"
wording: the local merge succeeded, but ``git push origin main`` was rejected
by branch protection ("no direct-push-to-main path", rules/git.md), leaving
local main one commit ahead of origin and forcing a manual recovery dance.
Step 10 must route the STATE.md refresh through a branch + PR like everything
else — the gate stays closed, STATE.md is not special-cased.

String-match ratchet on the skill text.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

LAIR_SKILL = (REPO / "skills" / "lair" / "SKILL.md").read_text()


def step_10() -> str:
    """The 'Refresh STATE.md' step, up to the next numbered step."""
    step = LAIR_SKILL.split("**Refresh STATE.md**", 1)[1]
    return step.split("\n11.", 1)[0]


def test_step_10_does_not_merge_locally_to_main():
    text = step_10()
    assert "fast-forward" not in text, (
        "lair step 10 must not instruct a local fast-forward merge to main — "
        "main is branch-protected and the follow-up push is rejected"
    )
    assert "merge to main" not in text.lower()


def test_step_10_does_not_push_main():
    assert "git push origin main" not in step_10(), (
        "lair step 10 must not push main directly — the GitHub gate rejects it"
    )


def test_step_10_routes_state_through_a_pr():
    text = step_10()
    assert "PR" in text, (
        "lair step 10 must open a PR for the STATE.md refresh and let it "
        "merge through the normal gate"
    )
    assert "push" in text.lower(), (
        "lair step 10 must push the throwaway branch so the PR can be opened"
    )
