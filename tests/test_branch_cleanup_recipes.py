"""Branch-cleanup recipes must not destroy live branches (ticket 0242).

Two documented recipes lost branches on 2026-06-10:

1. The stale-branch cleanup loop in ``rules/git.md`` ("Delete branches
   after merge") deletes any local branch that is an ancestor of
   origin/main — local ``main`` always is, and so is the branch you are
   standing on right after a merge. The recipe must skip ``main`` and the
   current branch explicitly, and use ``git branch -D`` (safe: the
   merge-base probe has just proven the branch is an ancestor of
   origin/main; ``-d`` checks merged-into-HEAD and spuriously refuses).

2. ``skills/roar/SKILL.md`` step 9b blanket-authorized ExitWorktree's
   ``discard_changes``, which also deletes the ORIGINAL branch the
   primary checkout returns to — orphaning unmerged commits at a
   detached HEAD. The step must require verifying the original branch is
   pushed or merged first, offer ``action: "keep"`` otherwise, and
   document the reflog recovery path.

These are string-match ratchets on the rule/skill text.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

GIT_RULES = (REPO / "rules" / "git.md").read_text()
ROAR_SKILL = (REPO / "skills" / "roar" / "SKILL.md").read_text()


def cleanup_recipe() -> str:
    """The fenced bash block of the 'Delete branches after merge' bullet."""
    bullet = GIT_RULES.split("**Delete branches after merge.**", 1)[1]
    return bullet.split("```bash", 1)[1].split("```", 1)[0]


def test_git_md_recipe_skips_main():
    recipe = cleanup_recipe()
    assert '[ "$b" = main ] && continue' in recipe, (
        "rules/git.md cleanup loop must skip local main — it is always an "
        "ancestor of origin/main and the loop would delete it"
    )


def test_git_md_recipe_skips_current_branch():
    recipe = cleanup_recipe()
    assert "--show-current" in recipe, (
        "rules/git.md cleanup loop must skip the current branch "
        "(guard via git branch --show-current)"
    )


def test_git_md_recipe_uses_force_delete_after_ancestor_probe():
    recipe = cleanup_recipe()
    assert 'git branch -D "$b"' in recipe, (
        "rules/git.md cleanup loop must use -D: -d checks merged-into-HEAD "
        "and silently skips branches whose upstream is gone; the "
        "merge-base --is-ancestor probe already proved the branch merged"
    )
    assert 'git branch -d "$b"' not in recipe


def test_roar_9b_checks_original_branch_before_discard():
    assert "ORIGINAL branch" in ROAR_SKILL, (
        "roar step 9b must require verifying the ORIGINAL branch (the one "
        "the primary checkout returns to) is pushed or merged before "
        "authorizing discard_changes"
    )
    assert "pushed or merged" in ROAR_SKILL


def test_roar_9b_offers_keep_for_unmerged_original():
    assert '`action: "keep"`' in ROAR_SKILL, (
        "roar step 9b must direct the agent to use action: \"keep\" when "
        "the original branch carries unmerged commits"
    )


def test_roar_9b_documents_reflog_recovery():
    assert "reflog" in ROAR_SKILL and "git switch -c" in ROAR_SKILL, (
        "roar step 9b must document the recovery path (reflog + "
        "git switch -c) for a branch deleted by discard_changes"
    )
