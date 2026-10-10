"""§ Merging in rules/git.md must delegate its recovery procedures, not inline
them (ticket 0907, 2026-09-10 — same pattern as test_branch_cleanup_recipes.py
for § Branch cleanup).

rules/git.md is resident in every session of every project; the multi-PR-wave
and generated-file-conflict recovery procedures are long enough to be worth
paying only in the sessions that run `/merge`. This is a string-match ratchet:
it proves the substance moved to skills/merge/SKILL.md and did not just get
duplicated there while the resident copy stayed fat.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _normalize(text: str) -> str:
    """Collapse whitespace so a phrase wrapped across source lines still matches."""
    return re.sub(r"\s+", " ", text)


GIT_RULES = _normalize((REPO / "rules" / "git.md").read_text())
MERGE_SKILL = _normalize((REPO / "skills" / "merge" / "SKILL.md").read_text())
GAZE_SKILL = _normalize((REPO / "skills" / "gaze" / "SKILL.md").read_text())


def test_git_md_points_at_merge_for_conflict_recovery():
    assert "/merge` § Merge conflict recovery" in GIT_RULES, (
        "rules/git.md § Merging must point at /merge for the multi-PR-wave "
        "and generated-file conflict recipes"
    )


def test_git_md_does_not_inline_the_conflict_recipes():
    # The distinctive long-form sentences that used to live in rules/git.md;
    # their presence here means the content was duplicated, not delegated.
    assert "don't hand-patch" not in GIT_RULES
    assert "regenerate to a scratch path" not in GIT_RULES


def test_merge_skill_carries_the_conflict_recipes():
    assert "don't hand-patch" in MERGE_SKILL, (
        "skills/merge/SKILL.md must carry the multi-PR-wave recovery recipe "
        "moved out of rules/git.md"
    )
    assert "regenerate to a scratch path" in MERGE_SKILL, (
        "skills/merge/SKILL.md must carry the generated-file conflict "
        "recovery recipe moved out of rules/git.md"
    )


def test_merge_skill_documents_repo_merge_method_drift():
    assert "Merge method drifts per repo" in MERGE_SKILL, (
        "skills/merge/SKILL.md must document that MERGE_FLAGS hardcodes "
        "--merge and that a squash-only repo will reject it"
    )


def test_gaze_states_branch_currency_as_a_caller_prerequisite():
    assert "Branch-currency prerequisite" in GAZE_SKILL, (
        "skills/gaze/SKILL.md must state, in its own Invariants, that the "
        "caller rebases onto current origin/main before invoking — /gaze "
        "does not rebase the PR branch itself"
    )
