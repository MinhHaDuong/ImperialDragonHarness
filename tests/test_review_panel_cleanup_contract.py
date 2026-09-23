"""Ticket 0948: review scratch has one owner and a bounded lifetime."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_standalone_review_pr_cleans_only_after_verified_post():
    text = (ROOT / "skills/review-pr/SKILL.md").read_text()
    cleanup = text.split("## Panel scratch cleanup", 1)[1]
    assert "verified" in cleanup.lower()
    assert 'rm -rf -- "$panel"' in cleanup
    assert '"$worktree/build/panel-head"' in cleanup
    assert "embedded by /gaze" in cleanup
    assert "leave the panel" in cleanup.lower()
    assert "do not gitignore" in cleanup.lower()


def test_gaze_owns_delegated_panel_cleanup_on_every_exit():
    text = (ROOT / "skills/gaze/SKILL.md").read_text()
    cleanup = text.split("## Review scratch cleanup", 1)[1]
    assert "every exit path" in cleanup.lower()
    assert '"$review_tree/.panel/<pr-number>"' in cleanup
    assert '"$review_tree/build/panel-head"' in cleanup
    assert "after" in cleanup.lower() and "consumed" in cleanup.lower()
    assert "circuit-breaker" in cleanup.lower()
