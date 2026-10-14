"""Branch-cleanup recipes must not destroy live branches (ticket 0242).

Two documented recipes lost branches on 2026-06-10:

1. Historical sweeps deleted branches outside the completed task. The current
   contract accepts only explicitly named completed-PR targets with their full
   approved head OIDs. Local cleanup keeps Git's ordinary merge/worktree refusal;
   drift is refused before deletion. Behavioral coverage lives in the shell test.

2. ``skills/roar/SKILL.md`` step 9b blanket-authorized ExitWorktree's
   ``discard_changes``, which also deleted the ORIGINAL branch. Sessions no
   longer enter worktrees through the runtime (ticket 1077), so step 9 removes
   the tree with plain ``git worktree remove`` and the hazard is gone.

The sweep itself moved into ``skills/roar/close-and-clean.sh`` (ticket 1084);
its guards are tested behaviourally in ``tests/test_roar_close_and_clean.sh``
by running the real script and stripping one guard at a time. What remains here
is a string-match ratchet on the rule text: the rule delegates the sweep.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

GIT_RULES = (REPO / "rules" / "git.md").read_text()
ROAR_SKILL = (REPO / "skills" / "roar" / "SKILL.md").read_text()


def test_git_md_delegates_the_sweep_and_inlines_no_loop():
    """The rule states the discipline; the procedure lives in the skill.

    A resident rule file is read in every session of every project, so 25 lines
    of shell there are paid by every conversation that will never run them
    (ticket 0572).
    """
    assert "```bash" not in GIT_RULES, (
        "rules/git.md must not inline shell recipes — the branch sweep is "
        "/roar step 10"
    )
    assert "/roar` step 10" in GIT_RULES, (
        "rules/git.md must point at the skill that owns the sweep"
    )


def test_roar_cleanup_requires_explicit_completed_task_targets():
    helper = (REPO / "skills/roar/close-and-clean.sh").read_text()
    assert "--local-branch" in helper and "--remote-branch" in helper
    assert "for-each-ref" not in helper, "roar must not enumerate cleanup candidates"
    assert "restore_branch" not in helper, "refuse drift before deleting"
    assert "git branch -D" not in helper, "retain ordinary Git merge refusal"
    assert "only the completed task" in ROAR_SKILL
