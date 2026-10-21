"""Ticket 0948: review scratch has one owner and a bounded lifetime."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gaze_owns_delegated_panel_cleanup_on_every_exit():
    text = (ROOT / "skills/gaze/SKILL.md").read_text()
    cleanup = text.split("## Review scratch cleanup", 1)[1].split("\n## ", 1)[0]
    assert "every exit path" in cleanup.lower()
    assert '"$review_tree/.panel/<pr-number>"' in cleanup
    assert '"$review_tree/build/panel-head"' in cleanup
    assert "after" in cleanup.lower() and "consumed" in cleanup.lower()
    assert "circuit-breaker" in cleanup.lower()
    assert 'worktree-exit-preflight.sh" --removal --branch "$PR_BRANCH" "$review_tree"' in cleanup
    assert cleanup.index('worktree-tmp-guard.py" removal') < cleanup.index('rm -rf -- "$review_tree/.panel/<pr-number>"')
    assert 'git -C "$primary_root" worktree remove "$review_tree"' in cleanup
    assert 'worktree remove "$review_tree" --force' not in cleanup
    assert "leave the review worktree" in " ".join(cleanup.lower().split())
