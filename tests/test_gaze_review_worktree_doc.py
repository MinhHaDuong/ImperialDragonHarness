"""Pin skills/gaze/SKILL.md's account of review-worktree guard coverage (ticket 0342).

The worktree-path guard (`scripts/pretooluse-worktree-path-guard.sh`) has no
`review-*` allowlist and never did: it allows an Edit/Write only when the acting
hook process is physically inside the worktree that contains the target path
(the `_in_worktree` identity predicate plus the `$worktree_root/*` prefix check),
with the narrow `projects/*/memory/*` exemption and the human-set
`GUARD_ALLOW_PRIMARY_EDIT` escape hatch. Ticket 0300 MOVED gaze review worktrees
from `/tmp` (outside every guard fast-path) into `.claude/worktrees/review-*` to
bring them UNDER that identity check — coverage, not a name-pattern whitelist.

The old SKILL.md comment "`.claude/worktrees/review-*` is already whitelisted"
overclaimed and contradicted the guard. This adherence test pins the corrected
account so the doc cannot drift back to the whitelist framing.

RED proof (2026-07-14): against the unmodified SKILL.md this test failed on the
missing corrected phrase; the correction (ticket 0342 Action 1) turns it green.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "gaze" / "SKILL.md"


@pytest.mark.adherence
def test_review_worktree_not_described_as_whitelisted():
    raw = SKILL.read_text(encoding="utf-8")
    # Collapse whitespace (incl. the `#`-comment line wraps) so the required
    # phrases still match if the comment block is reflowed across lines.
    text = " ".join(raw.replace("#", " ").split())
    assert "already whitelisted" not in text, (
        "skills/gaze/SKILL.md still claims review-* worktrees are 'already "
        "whitelisted' — the guard has no such allowlist (ticket 0342). It "
        "covers review-* via the same worktree-identity check as every "
        "worktree; edits are allowed only when the acting process is physically "
        "inside the worktree, never by path pattern."
    )
    # The corrected account must be present so the doc states the real model.
    assert "is not whitelisted by name" in text, (
        "skills/gaze/SKILL.md must state that .claude/worktrees/review-* is not "
        "whitelisted by name but covered by the worktree-identity check "
        "(ticket 0342)."
    )
    assert "physically inside that" in text, (
        "skills/gaze/SKILL.md must state that edits are allowed only when the "
        "acting process is physically inside the review worktree (ticket 0342)."
    )
