"""Hunt step 3 worktree ownership and the portable plain-git recipe (ticket 1076).

History:

Ticket 0294 (child of 0251): `Agent(isolation:"worktree")` names its worktree
`agent-<id>`, not `t<id>`, so a spawned execute agent invoking `Skill(hunt)`
failed step 3's exact-name ownership check and re-attempted `EnterWorktree`,
which hard-refuses from inside a worktree session.

Step 3 must now (a) accept the `agent-*` worktree the spawner created for this
agent session as OWNED, (b) still forbid a shared or `explore-*` worktree that
may host a live session (2026-06-11 incident), (c) treat an `EnterWorktree`
"already in a worktree" rejection in a spawned-agent context as confirmation,
and (d) point ad hoc orchestrators at the beat.py headless pattern.

Text-grep hygiene test — fast tier, no marker.
"""

import functools
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "hunt" / "SKILL.md"


@functools.cache
def step3_text() -> str:
    """Return step 3's body with whitespace collapsed to single spaces.

    Collapsing lets phrase assertions match regardless of where prose wraps
    across lines in the source.
    """
    text = SKILL.read_text()
    m = re.search(r"^3\.\s.*?(?=^4\.\s)", text, re.MULTILINE | re.DOTALL)
    assert m, "could not locate step 3 in hunt/SKILL.md"
    return re.sub(r"\s+", " ", m.group(0))


def test_plain_git_recipe_with_lock():
    """Ticket 1076: portable recipe, plain git plus a lock worktree-gc honours."""
    step3 = step3_text()
    assert "git worktree add .claude/worktrees/" in step3
    assert "git worktree lock" in step3
    assert "EnterWorktree" not in step3 and "isolation" not in step3


def test_lock_reason_matches_gc_dead_pid_rail():
    """The recipe's lock reason carries `(pid N`, the shape worktree-gc parses.

    Without it gc treats the lock as an opaque in-use marker and never
    reclaims the tree, even when the owner is long dead.
    """
    gc = (REPO / "scripts" / "worktree-gc.sh").read_text()
    m = re.search(r'=~ (\\\(pid\\ \(\[0-9\]\+\))', gc)
    assert m, "could not locate worktree-gc's lock-pid regex"
    regex = re.compile(r"\(pid ([0-9]+)")
    step3 = step3_text()
    r = re.search(r"git worktree lock\s+--reason\s+\"([^\"]*)\"", step3)
    assert r, "recipe lock must carry --reason \"...\""
    reason = re.sub(r"<[^>]*pid[^>]*>", "12345", r.group(1))
    assert regex.search(reason), f"reason {reason!r} would not match gc's regex"
    assert "$PPID" in step3, "recipe must say how to get the long-lived owner pid"


def test_shared_and_explore_worktrees_still_forbidden():
    """The 2026-06-11 shared-worktree protection is intact."""
    step3 = step3_text()
    assert "explore-*" in step3, "step 3 must still forbid `explore-*` worktrees"
    assert "2026-06-11" in step3, (
        "the 2026-06-11 shared-worktree incident rationale must stay in step 3"
    )
    assert "not owned" in step3.lower(), (
        "step 3 must still name the not-owned case for shared/explore worktrees"
    )


def test_clean_tree_gate_is_executable():
    """The agent-* ownership case names an executable cleanliness check."""
    step3 = step3_text()
    assert "git status --porcelain" in step3, (
        "step 3 must state `git status --porcelain` as the executable cleanliness "
        "gate for a handed-over worktree, not just the word 'clean' (ticket 0294)"
    )


def test_pid_discriminator_obtainable():
    """Step 3 spells out a literal, executable way to obtain the `$$` discriminator.

    Ticket 0309: `EnterWorktree`'s name schema rejects `$` characters, so the
    model must resolve the session PID to a literal before the call. Step 3 must
    show how (e.g. `bash -c 'echo $$'`), not just reference the bare `$$` token.
    """
    step3 = step3_text()
    assert "bash -c 'echo $$'" in step3, (
        "step 3 must show a literal, executable way to obtain the session-PID "
        "discriminator (e.g. `bash -c 'echo $$'`) "
        "so parallel sessions get distinct paths (ticket 0309)"
    )


def test_headless_pattern_pointer_present():
    """One sentence points ad hoc orchestrators at the headless spawn pattern.

    It named `beat.py` as the precedent until ticket 0882 removed it. The
    assertion on the precedent went with it; the one that matters -- that step 3
    still hands orchestrators the invocation instead of a hand-typed contract --
    is what remains, and is the reason this test exists.
    """
    step3 = step3_text()
    assert 'claude -p "/hunt' in step3, (
        "step 3 must point ad hoc orchestrators at the `claude -p \"/hunt <id>\"` "
        "headless pattern, instead of hand-typed ownership contracts"
    )
