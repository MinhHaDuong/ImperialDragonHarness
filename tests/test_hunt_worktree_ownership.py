"""Hunt step 3 recognizes a spawner-created `agent-*` worktree as owned.

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


def test_agent_worktree_is_owned():
    """The generalized predicate accepts the spawner's `agent-*` worktree."""
    step3 = step3_text()
    assert "agent-*" in step3, (
        "step 3 must recognize the spawner-created `agent-*` worktree as owned "
        "(ticket 0294); the exact-`t$ARGUMENTS`-only check rejected raid execute "
        "agents"
    )


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
        "gate for the agent-* ownership case, not just the word 'clean' (ticket 0294)"
    )


def test_rejection_as_confirmation_documented():
    """An `EnterWorktree` rejection in a spawned context is confirmation."""
    step3 = step3_text()
    assert "already in a worktree" in step3, (
        "step 3 must mention the `EnterWorktree` 'already in a worktree' rejection"
    )
    assert re.search(r"confirm", step3, re.IGNORECASE), (
        "step 3 must document the rejection-as-confirmation branch (ticket 0294)"
    )


def test_headless_pattern_pointer_present():
    """One sentence points ad hoc orchestrators at the beat.py headless pattern."""
    step3 = step3_text()
    assert 'claude -p "/hunt' in step3, (
        "step 3 must point ad hoc orchestrators at the `claude -p \"/hunt <id>\"` "
        "headless pattern that beat.py uses, instead of hand-typed contracts"
    )
    assert "beat.py" in step3, "step 3 should name beat.py as the headless precedent"
